"""Verify only the separately approved aggregate official-test length payload."""
import hashlib
import json
from pathlib import Path
import sys

SOURCE = 'data/raw/promptshield/a5234cb1f5cdb256600cab64b8c961195b5e8404/test.json'
SOURCE_SHA = '526207c2485829d9961407011d7f4cd929569e7f285dc8396b3f385e0608bc70'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_bytes())
    require(isinstance(manifest, dict) and manifest.get('scope') ==
            'Aggregate official-test token lengths only; no model, cap comparisons, identities or credential exports',
            'Administrative stage scope mismatch')
    require(isinstance(manifest.get('files'), dict) and SOURCE in manifest['files'], 'Missing pinned source inventory')
    require(manifest['files'][SOURCE]['sha256'] == SOURCE_SHA, 'Unapproved official-test source identity')
    total = 0
    for relative, expected in manifest['files'].items():
        path = root / relative
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts, 'Unsafe stage path')
        require(path.resolve().is_relative_to(root) and path.is_file() and not path.is_symlink(), 'Missing or redirected stage member')
        require(path.name not in ('train.json', 'validation.json', 'test-a.jsonl', 'test-b.jsonl', 'model.safetensors', 'token'),
                'Forbidden administrative stage member')
        require(path.name != 'test.json' or relative == SOURCE, 'Unapproved test source path')
        raw = path.read_bytes()
        require(len(raw) == expected['bytes'], 'Stage size mismatch')
        require(hashlib.sha256(raw).hexdigest() == expected['sha256'], 'Stage hash mismatch')
        total += len(raw)
    require(total == manifest['total_bytes'], 'Stage total size mismatch')
    print(json.dumps({'verified_stage_files': len(manifest['files']), 'verified_bytes': total,
                      'scope': 'aggregate official-test lengths only', 'classifier_weights_included': False}))


if __name__ == '__main__':
    verify(sys.argv[1])
