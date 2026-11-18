"""Network-free download checks using a synthetic token, never a local Hub login."""
import hashlib
import io
import unittest

from precision_benchmark.contract_audit import AuditError
from scripts.fetch_pilot_checkpoint import copy_checkpoint


TOKEN = "hf_SYNTHETIC_ONLY_NO_SECRET"


class ChunkStream:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.reads = []

    def read(self, count, decode_content):
        self.reads.append((count, decode_content))
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if isinstance(chunk, Exception):
            raise chunk
        if len(chunk) > count:
            self.chunks.insert(0, chunk[count:])
        return chunk[:count]


def digest(body):
    return hashlib.sha256(body).hexdigest()


class CheckpointStreamTests(unittest.TestCase):
    def test_valid_payload_survives_short_reads_and_tail_flush(self):
        body = bytes(range(256)) * 3
        for width in (1, 7, len(TOKEN) - 1, 97, len(body)):
            with self.subTest(width=width):
                raw = ChunkStream([body[i:i + width] for i in range(0, len(body), width)])
                output = io.BytesIO()
                self.assertEqual(copy_checkpoint(raw, output, TOKEN, len(body), digest(body)),
                                 (len(body), digest(body)))
                self.assertEqual(output.getvalue(), body)
                self.assertTrue(all(0 < size <= 4 * 1024 * 1024 and not decode
                                    for size, decode in raw.reads))

    def test_reflection_at_every_two_chunk_boundary_is_rejected_before_retention(self):
        secret = TOKEN.encode("ascii")
        prefix = b"." * 80
        for split in range(1, len(secret)):
            with self.subTest(split=split):
                body = prefix + secret + b"end"
                output = io.BytesIO()
                raw = ChunkStream([prefix + secret[:split], secret[split:] + b"end"])
                with self.assertRaises(AuditError) as error:
                    copy_checkpoint(raw, output, TOKEN, len(body), digest(body))
                self.assertNotIn(TOKEN, str(error.exception))
                self.assertTrue(output.getvalue())
                self.assertEqual(set(output.getvalue()), {ord(".")})

    def test_same_chunk_and_one_byte_reads_reject_reflection(self):
        body = b"." * 80 + TOKEN.encode("ascii") + b"end"
        cases = ([body], [bytes([byte]) for byte in body])
        for chunks in cases:
            with self.subTest(chunks=len(chunks)):
                output = io.BytesIO()
                with self.assertRaises(AuditError):
                    copy_checkpoint(ChunkStream(chunks), output, TOKEN, len(body), digest(body))
                self.assertLessEqual(set(output.getvalue()), {ord(".")})

    def test_interrupted_stream_keeps_possible_token_prefix_in_memory(self):
        output = io.BytesIO()
        raw = ChunkStream([b"." * 80 + TOKEN.encode("ascii")[:12], OSError("synthetic failure")])
        with self.assertRaises(OSError):
            copy_checkpoint(raw, output, TOKEN, 200, "0" * 64)
        self.assertTrue(output.getvalue())
        self.assertEqual(set(output.getvalue()), {ord(".")})

    def test_wrong_size_or_digest_does_not_flush_unverified_tail(self):
        body = b"." * 80
        for expected_size, expected_sha in ((79, digest(body)), (81, digest(body)), (80, "0" * 64)):
            with self.subTest(expected_size=expected_size, expected_sha=expected_sha):
                output = io.BytesIO()
                with self.assertRaises(ValueError):
                    copy_checkpoint(ChunkStream([body]), output, TOKEN, expected_size, expected_sha)
                self.assertLess(len(output.getvalue()), len(body))


if __name__ == "__main__":
    unittest.main()
