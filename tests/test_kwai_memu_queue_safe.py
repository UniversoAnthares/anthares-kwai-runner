import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import kwai_memu_queue_safe as memu
import kwai_device_failover_worker as worker


class MemuProofTests(unittest.TestCase):
    def test_new_profile_card_requires_fresh_identity(self):
        pub=SimpleNamespace(cfg=SimpleNamespace(verify_timeout=60),verify_identity=Mock(),
            profile_fingerprints=Mock(return_value=['new','a','b']))
        with patch.object(memu.time,'monotonic',side_effect=[0,1]):
            ok,proof=memu.QueuePublisher.verify_after_post(pub,['a','b','c'])
        self.assertTrue(ok)
        pub.verify_identity.assert_called_once()
        self.assertEqual(proof,'memu-exact-identity-new-profile-card')

    def test_unchanged_profile_never_confirms(self):
        pub=SimpleNamespace(cfg=SimpleNamespace(verify_timeout=60),verify_identity=Mock(),
            profile_fingerprints=Mock(return_value=['a','b','c']))
        with patch.object(memu.time,'monotonic',side_effect=[0,1,61]),patch.object(memu.time,'sleep'):
            self.assertFalse(memu.QueuePublisher.verify_after_post(pub,['a','b','c'])[0])

    def test_standby_prepares_before_started_and_commit(self):
        events=[]
        with patch.dict(worker.os.environ,{'KWAI_QUEUE_JOB_ID':'test-job','KWAI_VIDEO_URL':'https://example.invalid/video'}), \
             patch.object(worker,'retry_pending_ack',return_value=None), \
             patch.object(worker,'load_health',return_value={}), \
             patch.object(worker,'AndroidExecutorRouter'), \
             patch.object(worker,'merge_health',return_value={}), \
             patch.object(worker.routing,'load_manifest',return_value={}), \
             patch.object(worker.routing,'choose',return_value='memu_android'), \
             patch.object(worker,'download_media',return_value=Path('missing-test-media')), \
             patch.object(worker,'prepare_memu',side_effect=lambda _: (events.append('prepare') or True,'',{})), \
             patch.object(worker,'queue_callback',side_effect=lambda *a: (events.append(a[0]) or True,'')), \
             patch.object(worker,'commit_memu',side_effect=lambda _: (events.append('commit') or True,'')), \
             patch.object(worker,'record_result'), \
             patch.object(worker,'finalize_verified_publish',return_value=0):
            self.assertEqual(worker.main(),0)
        self.assertEqual(events,['prepare','started','commit'])
