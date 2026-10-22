"""Pinterest editorial QA must isolate a failing clip and progress to the next."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import cortes_pinterest_metadata_qa as qa


class PerClipIsolation(unittest.TestCase):
    def test_unexpected_decoder_error_does_not_block_next_clip(self):
        with tempfile.TemporaryDirectory() as temp:
            jobs=[
                {"id":"cortes-fanout-pinterest-"+("a"*32),"media_url":"https://anthares.us/a.mp4","source_title":"Original","segment_id":"seg1"},
                {"id":"cortes-fanout-pinterest-"+("b"*32),"media_url":"https://anthares.us/b.mp4","source_title":"Original","segment_id":"seg2"}]
            def api(kind, payload):
                if kind=="metadata-pending":
                    return {"ok":True,"jobs":jobs}
                if kind=="metadata-enrich":
                    return {"ok":True}
                raise AssertionError(kind)
            accepted={"title":"Análise da linguagem literária ● Universo Anthares","description":"desc","keywords":["linguagem","literatura","análise"],"hashtags":["#literatura","#analise"]}
            with patch.object(qa,"CACHE",Path(temp)/"transcripts"),patch.object(qa,"call",side_effect=api) as api_mock,patch.object(qa,"approved_media",return_value=True),patch.object(qa,"media_status",return_value=200),patch.object(qa,"transcript",side_effect=[TypeError("decoder"),"Transcrição real de teste."*8]),patch.object(qa,"strategic_metadata",return_value=accepted),patch.object(qa,"qa_incident") as alert,patch("builtins.print"):
                result=qa.metadata_qa(2)
            self.assertEqual(result,1)
            alert.assert_any_call("PINTEREST_METADATA_TYPEERROR")
            self.assertEqual(len([c for c in api_mock.call_args_list if c.args[0]=="metadata-enrich"]),1)
            self.assertTrue((Path(temp)/".pinterest-qa-title-cursor").exists())

    def test_invalid_media_is_isolated(self):
        with tempfile.TemporaryDirectory() as temp:
            jobs=[
                {"id":"cortes-fanout-pinterest-"+("a"*32),"media_url":"bad","source_title":"Live","segment_id":"a"},
                {"id":"cortes-fanout-pinterest-"+("b"*32),"media_url":"bad","source_title":"Live","segment_id":"b"}]
            with patch.object(qa,"CACHE",Path(temp)/"transcripts"),patch.object(qa,"call",return_value={"ok":True,"jobs":jobs}),patch.object(qa,"approved_media",return_value=False),patch.object(qa,"qa_incident") as alert,patch("builtins.print"):
                self.assertEqual(qa.metadata_qa(2),0)
            self.assertEqual(alert.call_count,2)
            alert.assert_any_call("PINTEREST_METADATA_VALUEERROR")


if __name__=="__main__":
    unittest.main()
