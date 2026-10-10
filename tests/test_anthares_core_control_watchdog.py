import json
import tempfile
import unittest
from pathlib import Path
from anthares_core.control_watchdog import supervise

class ControlWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"watchdog.json"
        self.calls=[]
    def tearDown(self):self.tmp.cleanup()
    def deploy(self):self.calls.append("deploy")
    def test_healthy_does_not_redeploy(self):
        result=supervise(self.path,check=lambda:True,redeploy=self.deploy,now=10000,delay=lambda n:None)
        self.assertEqual(result["status"],"HEALTHY")
        self.assertEqual(self.calls,[])
    def test_three_failed_checks_dispatch_once(self):
        checks=[]
        def down():checks.append(1);return False
        result=supervise(self.path,check=down,redeploy=self.deploy,now=10000,delay=lambda n:None)
        self.assertEqual(result["status"],"RECOVERY_DISPATCHED")
        self.assertEqual(len(checks),3)
        self.assertEqual(self.calls,["deploy"])
    def test_persisted_cooldown_blocks_repeated_redeploy(self):
        supervise(self.path,check=lambda:False,redeploy=self.deploy,now=10000,delay=lambda n:None)
        result=supervise(self.path,check=lambda:False,redeploy=self.deploy,now=10500,delay=lambda n:None)
        self.assertEqual(result["status"],"RECOVERY_THROTTLED")
        self.assertEqual(self.calls,["deploy"])
    def test_dispatch_failure_does_not_mark_success(self):
        def fail():raise RuntimeError("unavailable")
        result=supervise(self.path,check=lambda:False,redeploy=fail,now=10000,delay=lambda n:None)
        self.assertEqual(result["status"],"RECOVERY_DISPATCH_FAILED")
        self.assertNotIn("last_dispatch_at",json.loads(self.path.read_text()))
    def test_transient_failure_recovers_without_dispatch(self):
        checks=iter([False,False,True])
        result=supervise(self.path,check=lambda:next(checks),redeploy=self.deploy,now=10000,delay=lambda n:None)
        self.assertTrue(result["healthy"])
        self.assertEqual(self.calls,[])

if __name__=="__main__":unittest.main()
