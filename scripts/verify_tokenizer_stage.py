"""Verify the explicitly selected, credential-free tokenizer job payload."""
import hashlib
import json
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_bytes())
    require(isinstance(manifest, dict) and manifest.get('scope') ==
            'CPU tokenizer audit; development data only; no model weights or credentials',
            'Stage scope mismatch')
    require(isinstance(manifest.get('files'), dict) and bool(manifest['files']), 'Stage has no file inventory')
    total = 0
    for relative, expected in manifest['files'].items():
        path = root / relative
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'Unsafe stage member path')
        require(path.resolve().is_relative_to(root) and path.is_file() and not path.is_symlink(),
                'Stage member missing or redirected')
        require(path.name not in ('test.json', 'test-a.jsonl', 'test-b.jsonl', 'model.safetensors', 'token'),
                'Forbidden stage member')
        raw = path.read_bytes()
        require(len(raw) == expected['bytes'], 'Stage member size mismatch')
        require(hashlib.sha256(raw).hexdigest() == expected['sha256'], 'Stage member hash mismatch')
        total += len(raw)
    require(total == manifest['total_bytes'], 'Stage total size mismatch')
    print(json.dumps({'verified_stage_files': len(manifest['files']), 'verified_bytes': total,
                      'official_test_or_tensor_payload_included': False}))


if __name__ == '__main__':
    verify(sys.argv[1])
