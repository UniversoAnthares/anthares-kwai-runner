import unittest
from unittest.mock import patch,call
from anthares_publisher.editorial import require_strategic_master
from tools import cortes_buffer_pinterest_cloud as p
from pathlib import Path

class PreflightIsolatedNotBlocking(unittest.TestCase):
    def test_portuguese_hashtags_pass_runtime_validator(self):
        payload={
          "segment_id":"g1:fOmihuHUT1M:1:60",
          "editorial_policy":"anthares_editorial_transcript_v2",
          "title":"O Mistério da Transformação de Gregor Samsa ● Universo Anthares",
          "description":"Neste trecho a transformação de Gregor muda as relações familiares, questionando a responsabilidade e a percepção dos leitores de Kafka.",
          "keywords":["Kafka","Gregor Samsa","Metamorfose","interpretação"],
          "hashtags":["#CríticaLiterária","#Kafka","#Metamorfose"]
        }
        self.assertIsNone(require_strategic_master(payload))

    def test_one_invalid_clip_quarantined_and_next_cut_scheduled(self):
        jobs=[{"id":"clip_bad","lease_generation":1},
              {"id":"clip_good","lease_generation":2}]
        actions=[]
        def queue(action,payload=None):
            actions.append(action)
            if action=="lease":
                return {"job":jobs.pop(0),"delivery_route":"buffer"}
            return {"ok":True}
        payload={"platform":"pinterest","media_url":"https://anthares.us/wp-content/uploads/anthares-clips/a.mp4"}
        with patch.object(p,"queue",side_effect=queue),\
             patch.object(p,"safe_payload",return_value=payload),\
             patch("social_adapters.buffer_three_channels.prepare",
                   side_effect=[ValueError("CORTES_HASHTAGS_MISSING"),None]),\
             patch.object(p,"is_media_missing",return_value=False),\
             patch.object(p,"schedule",return_value={"status":"SCHEDULED_IN_BUFFER","remote_id":"0123456789abcdef01234567"}) as schedule,\
             patch.object(p,"notify_editorial_p0") as qa:
            self.assertEqual(p.publish_once(),"SCHEDULED_IN_BUFFER")
        self.assertEqual(actions,["lease","editorial-invalid","lease","start","scheduled"])
        qa.assert_called_once_with("clip_bad","CORTES_HASHTAGS_MISSING")
        schedule.assert_called_once()

    def test_three_consecutive_bad_clips_have_bounded_attempts(self):
        jobs=[{"id":"bad"+str(i),"lease_generation":i+1} for i in range(3)]
        acts=[]
        def queue(action,payload=None):
            acts.append(action)
            if action=="lease":return {"job":jobs.pop(0),"delivery_route":"buffer"}
            return {"ok":True}
        with patch.object(p,"queue",side_effect=queue),\
             patch.object(p,"safe_payload",return_value={"media_url":"https://anthares.us/wp-content/uploads/anthares-clips/a.mp4"}),\
             patch("social_adapters.buffer_three_channels.prepare",side_effect=ValueError("CORTES_HASHTAGS_MISSING")) ,\
             patch.object(p,"notify_editorial_p0"),\
             patch.object(p,"schedule") as schedule:
            self.assertEqual(p.publish_once(),"EDITORIAL_QUARANTINE_BATCH_LIMIT")
        self.assertEqual(acts.count("lease"),3)
        self.assertEqual(acts.count("editorial-invalid"),3)
        schedule.assert_not_called()

    def test_neon_quarantine_requires_live_lease_with_no_upload(self):
        root=Path(__file__).resolve().parents[1]
        neon=(root/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf8")
        self.assertIn("if(verb==='editorial-invalid')",neon)
        self.assertIn("status='leased' AND remote_id IS NULL",neon)
        self.assertIn("publication_started_at IS NULL",neon)
        self.assertIn("lease_generation=$4 AND lease_until>now()",neon)
        self.assertIn("to_jsonb('requires_transcript_qa'::text)",neon)
        self.assertIn("editorial_invalid_qa",neon)
        self.assertIn("confirmation_evidence=CASE WHEN p.confirmation_evidence->>'kind'='editorial_invalid_qa'",neon)
if __name__=="__main__":unittest.main()
