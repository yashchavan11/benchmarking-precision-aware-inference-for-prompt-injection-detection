"""Validate the explicit code/text-free-pilot stage before native execution."""
import hashlib
import json
from pathlib import Path
import sys

SCOPE = "P1-B code and text-free training pilot; no raw data, weights or credentials"

def verify(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_bytes())
    if manifest.get("scope") != SCOPE or not isinstance(manifest.get("files"), dict) or not manifest["files"]:
        raise ValueError("Invalid stage scope/inventory")
    total = 0
    for relative, expected in manifest["files"].items():
        path = root / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts or path.is_symlink():
            raise ValueError("Unsafe stage member")
        path.resolve().relative_to(root)
        if not path.is_file() or path.name in ("train.json", "validation.json", "test.json", "test-a.jsonl", "test-b.jsonl", "model.safetensors", "token"):
            raise ValueError("Missing or forbidden stage member")
        raw = path.read_bytes()
        if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
            raise ValueError("Stage content integrity failed")
        total += len(raw)
    if total != manifest["total_bytes"]:
        raise ValueError("Stage size mismatch")
    expected_files = set(manifest["files"]) | {manifest_path.name}
    actual_files = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Stage contains a redirected member")
        if path.is_file():
            actual_files.add(path.relative_to(root).as_posix())
    if actual_files != expected_files:
        raise ValueError("Stage has unlisted or missing files")
    return {"status":"verified", "files":len(manifest["files"]), "bytes":total,"scope":SCOPE}

if __name__ == "__main__":
    print(json.dumps(verify(sys.argv[1])))
