import unittest
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[1]/"tools"/"cortes_pinterest_metadata_qa.py")

class BoundedPinterestASR(unittest.TestCase):
    def test_media_decode_bounded_before_whisper(self):
        source=SOURCE.read_text(encoding="utf8")
        self.assertIn("'-rw_timeout','12000000'",source)
        self.assertIn("timeout=100",source)
        self.assertIn("WHISPER.transcribe(wav",source)
        self.assertNotIn("WHISPER.transcribe(url",source)
        self.assertIn("PINTEREST_ASR_SOURCE_TIMEOUT",source)
    def test_transcript_cache_retained_without_partial_write(self):
        source=SOURCE.read_text(encoding="utf8")
        self.assertIn("with TemporaryDirectory(",source)
        self.assertIn("filepath.write_text(text",source)

if __name__=="__main__":
    unittest.main()
