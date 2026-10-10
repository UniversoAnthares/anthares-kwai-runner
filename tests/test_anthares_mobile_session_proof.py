import unittest
from anthares_mobile.session_proof import SCHEMA,validate

def observation(run):
    return dict(schema=SCHEMA,run_id=str(run),platform="kwai",
                observed_account="lucasrosalem",profile_visible=True,
                login_prompt_visible=False,relaunch_verified=True,
                fresh_runner=True,session_fingerprint="a"*64)

class SessionProofTests(unittest.TestCase):
    def test_two_independent_observations(self):
        self.assertTrue(validate([observation(1),observation(2)])["ui_session_continuity"])
    def test_rejects_same_run(self):
        with self.assertRaises(ValueError): validate([observation(1),observation(1)])
    def test_rejects_missing_identity(self):
        x=observation(2);x["observed_account"]="other"
        with self.assertRaises(ValueError): validate([observation(1),x])
    def test_rejects_different_session(self):
        x=observation(2);x["session_fingerprint"]="b"*64
        with self.assertRaises(ValueError): validate([observation(1),x])
    def test_rejects_no_relaunch(self):
        x=observation(2);x["relaunch_verified"]=False
        with self.assertRaises(ValueError): validate([observation(1),x])
    def test_rejects_login_prompt(self):
        x=observation(2);x["login_prompt_visible"]=True
        with self.assertRaises(ValueError): validate([observation(1),x])
    def test_rejects_untrusted_runner(self):
        x=observation(2);x["fresh_runner"]=False
        with self.assertRaises(ValueError): validate([observation(1),x])
