"""Retrieve the one approved pinned weight file using existing private Hub login.

No credential arguments, provider URLs, response bodies or exception text are logged.
The header-only audit keeps its original, narrower scope.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urljoin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from precision_benchmark.contract_audit import BoundedTransport, BASE, REVISION, origin, no_reflection

SIZE = 1192138968
SHA = "19701022d11e38d39bd77aed7263d2e9ce3a45ae29305248ef3de585f947511c"

def copy_checkpoint(raw, handle, token, expected_size, expected_sha):
    """Retain only checked bytes, including across arbitrary network read boundaries."""
    if not token:
        raise ValueError("Existing local Hub credential required")
    overlap = len(token.encode("ascii")) - 1
    pending = b""
    h, count = hashlib.sha256(), 0
    while True:
        chunk = raw.read(min(4 * 1024 * 1024, expected_size - count + 1), decode_content=False)
        if not chunk:
            break
        count += len(chunk)
        if count > expected_size:
            raise ValueError("Oversized weights")
        checked = pending + chunk
        no_reflection(checked, token)
        h.update(chunk)
        safe_end = max(0, len(checked) - overlap)
        handle.write(checked[:safe_end])
        pending = checked[safe_end:]
    if count != expected_size or h.hexdigest() != expected_sha:
        raise ValueError("Weight integrity failed")
    handle.write(pending)
    return count, h.hexdigest()


def fetch(output):
    from huggingface_hub import get_token
    token = get_token()
    if not token:
        raise ValueError("Existing local Hub credential required")
    output.mkdir(parents=True, exist_ok=False)
    transport = BoundedTransport(token)
    url = BASE + "model.safetensors"
    headers = {"Authorization": "Bearer " + token, "Accept-Encoding": "identity",
               "User-Agent": "precision-benchmark-pinned-weight-fetch/1"}
    try:
        for attempt in range(6):
            old_origin = origin(url)
            req = transport.request_factory("GET", url, headers=headers).prepare()
            settings = transport.settings_factory(url)
            if settings["verify"] in (False, None):
                raise ValueError("TLS verification required")
            response = transport.adapter.send(req, stream=True, timeout=(15, 60),
                verify=settings["verify"], cert=settings["cert"], proxies=settings["proxies"])
            try:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location", "")
                    no_reflection(unquote(location), token)
                    next_url = urljoin(url, location)
                    if origin(next_url) != old_origin:
                        headers.pop("Authorization", None)
                    url = next_url
                    continue
                if response.status_code != 200:
                    raise ValueError("Pinned weight HTTP request failed")
                if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                    raise ValueError("Unexpected encoding")
                length = response.headers.get("Content-Length")
                if length is not None and int(length) != SIZE:
                    raise ValueError("Wrong declared weight size")
                commit = response.headers.get("X-Repo-Commit")
                if commit is not None and commit != REVISION:
                    raise ValueError("Wrong revision header")
                partial = output / "model.safetensors.partial"
                with partial.open("xb") as handle:
                    count, digest = copy_checkpoint(response.raw, handle, token, SIZE, SHA)
                partial.rename(output / "model.safetensors")
                receipt = {"status":"complete", "revision":REVISION, "source_url":BASE+"model.safetensors",
                    "bytes":count,"sha256":digest,"redirects":attempt,
                    "retrieved_utc":datetime.now(timezone.utc).isoformat(),
                    "credentials_retained":False}
                (output/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
                print("Complete: pinned checkpoint size and full SHA-256 verified", flush=True)
                return
            finally:
                response.close()
        raise ValueError("Redirect limit")
    finally:
        transport.close()

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    try:
        fetch(args.output)
    except Exception:
        # Never reflect a signed URL, proxy value, credential or provider exception.
        print("Checkpoint fetch failed; preserve partial output and diagnose safely.",file=sys.stderr)
        sys.exit(1)
