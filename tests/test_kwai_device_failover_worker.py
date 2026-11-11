import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kwai_device_failover_worker as worker
import kwai_native_cortes as native
import xml.etree.ElementTree as ET


class KwaiDeviceFailoverWorkerTests(unittest.TestCase):
    def test_adb_failure_is_device_failure(self):
        self.assertEqual(worker.classify_failure("adb: device offline", 70), "device")

    def test_ui_timeout_is_device_failure(self):
        self.assertEqual(worker.classify_failure("uiautomator timed out", 79), "device")

    def test_policy_never_enters_device_failover(self):
        self.assertEqual(worker.classify_failure("content policy rejected", 70), "platform")

    def test_human_verification_never_enters_device_failover(self):
        self.assertEqual(worker.classify_failure("human-verification", 91), "platform")

    def test_irreversible_boundary_is_uncertain(self):
        self.assertEqual(worker.classify_failure("STATE=PUBLISH_REQUESTED", 90), "uncertain")

    def test_health_opens_circuit_after_three_device_failures(self):
        original = worker.STATE_PATH
        try:
            with tempfile.TemporaryDirectory() as td:
                worker.STATE_PATH = Path(td) / "health.json"
                h = {}
                worker.record_result(h, "physical_android", False, "device", "one")
                worker.record_result(h, "physical_android", False, "device", "two")
                worker.record_result(h, "physical_android", False, "device", "three")
                self.assertEqual(h["physical_android"]["consecutive_failures"], 3)
                self.assertTrue(h["physical_android"]["degraded"])
                worker.record_result(h, "physical_android", True)
                self.assertEqual(h["physical_android"]["consecutive_failures"], 0)
                self.assertFalse(h["physical_android"]["degraded"])
        finally:
            worker.STATE_PATH = original

    def test_queue_callback_requires_json_argv(self):
        with patch.dict(os.environ, {"ANTHARES_QUEUE_STARTED_COMMAND_JSON": '["python","callback.py"]'}):
            self.assertEqual(worker.callback_argv("started"), ["python", "callback.py"])

    def test_queue_callback_rejects_shell_string(self):
        with patch.dict(os.environ, {"ANTHARES_QUEUE_STARTED_COMMAND_JSON": "python callback.py"}):
            with self.assertRaises(RuntimeError):
                worker.callback_argv("started")

    def test_published_pending_ack_is_persisted_before_callback_repair(self):
        original = worker.ACK_PATH
        try:
            with tempfile.TemporaryDirectory() as td:
                worker.ACK_PATH = Path(td) / "ack.json"
                worker.mark_pending_ack("job-1", "physical_android")
                state = worker.load_ack_state()
                self.assertEqual(state["job-1"]["state"], "published_pending_ack")
                self.assertEqual(state["job-1"]["executor"], "physical_android")
                worker.mark_acknowledged("job-1")
                state = worker.load_ack_state()
                self.assertEqual(state["job-1"]["state"], "completed_acknowledged")
        finally:
            worker.ACK_PATH = original

    def test_retry_pending_ack_never_republishes(self):
        original = worker.ACK_PATH
        try:
            with tempfile.TemporaryDirectory() as td:
                worker.ACK_PATH = Path(td) / "ack.json"
                worker.mark_pending_ack("job-2", "memu_android")
                with patch.object(worker, "queue_callback", return_value=(True, "ok")) as callback:
                    self.assertEqual(worker.retry_pending_ack("job-2"), 0)
                callback.assert_called_once_with("complete", "memu_android")
                self.assertEqual(worker.load_ack_state()["job-2"]["state"], "completed_acknowledged")
        finally:
            worker.ACK_PATH = original



class KwaiNativeUiRecoveryTests(unittest.TestCase):
    def test_profile_duplicate_id_picks_rightmost_tappable_node(self):
        root=ET.Element('hierarchy')
        rid=native.RID_PROFILE
        ET.SubElement(root,'node',{'resource-id':rid,'bounds':'[648,2059][864,2134]','clickable':'true','enabled':'true'})
        ET.SubElement(root,'node',{'resource-id':rid,'bounds':'[864,2059][1080,2134]','clickable':'true','enabled':'true'})
        with patch.object(native,'dump',return_value=(root,Path('synthetic.xml'))):
            _,selected,_=native.wait('device',rid,'synthetic',seconds=2)
        self.assertEqual(native.center(selected.attrib['bounds']),(972,2096))

    def test_notification_offer_is_dismissed_without_enabling_notifications(self):
        modal=ET.Element('hierarchy')
        ET.SubElement(modal,'node',{'resource-id':'kwai.lite.video.basis:id/tv_dialog_title','text':'Ative as notificações instantâneas'})
        close=ET.SubElement(modal,'node',{'resource-id':'kwai.lite.video:id/iv_close','clickable':'true','bounds':'[983,692][1038,747]'})
        home=ET.Element('hierarchy')
        ET.SubElement(home,'node',{'resource-id':native.RID_PROFILE,'clickable':'true','enabled':'true','bounds':'[864,2059][1080,2134]'})
        with patch.object(native,'dump',side_effect=[(modal,Path('modal.xml')),(home,Path('home.xml'))]),patch.object(native,'tap') as tap,patch.object(native.time,'sleep'):
            _,selected,_=native.wait('device',native.RID_PROFILE,'synthetic',seconds=2)
        tap.assert_called_once_with('device',close)
        self.assertEqual(native.center(selected.attrib['bounds'])[0],972)


    def test_verification_uses_actual_attempt_time_not_current_time(self):
        from datetime import datetime
        st_time=int(datetime(2026,11,11,10,19).timestamp())
        baseline={'caption':'older unrelated entry','post_time':'2026-11-10 09:21 AM'}
        expected='Kafka e o simbolo do inseto na Metamorfose www.anthares.us - Universo Anthares'
        published={'account':'lucasrosalem','caption':'Kafka e o simbolo do inseto na Metam...','post_time':'2026-11-11 10:19 AM'}
        with patch.object(native,'latest',return_value=published),patch.object(native.time,'sleep'):
            found,_,proof=native.confirm('fixture',baseline,tries=1,delay=0,attempted_at=st_time,expected_caption=expected)
        self.assertTrue(found)
        self.assertEqual(proof,'profile-account-post-time-and-caption-prefix')
        published['caption']='Unrelated entry at the same time'
        with patch.object(native,'latest',return_value=published),patch.object(native.time,'sleep'):
            found,_,_=native.confirm('fixture',baseline,tries=1,delay=0,attempted_at=st_time,expected_caption=expected)
        self.assertFalse(found)

if __name__ == "__main__":
    unittest.main(verbosity=2)
