import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.verify_pilot_stage import SCOPE, verify

class StageTests(unittest.TestCase):
    def test_valid_content_and_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            data=b"permitted synthetic fixture\n"
            (root/"fixture.json").write_bytes(data)
            manifest={"scope":SCOPE,"files":{"fixture.json":{"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}},"total_bytes":len(data)}
            (root/"stage.json").write_text(json.dumps(manifest))
            self.assertEqual(verify(root/"stage.json")["status"],"verified")
            (root/"unlisted.txt").write_bytes(b"unexpected")
            with self.assertRaises(ValueError): verify(root/"stage.json")
            (root/"unlisted.txt").unlink()
            (root/"fixture.json").write_bytes(b"changed")
            with self.assertRaises(ValueError): verify(root/"stage.json")
    def test_forbidden_member(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"test.json").write_bytes(b"{}"); raw=b"{}"
            manifest={"scope":SCOPE,"files":{"test.json":{"bytes":2,"sha256":hashlib.sha256(raw).hexdigest()}},"total_bytes":2}
            (root/"stage.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError): verify(root/"stage.json")

if __name__ == "__main__": unittest.main()
