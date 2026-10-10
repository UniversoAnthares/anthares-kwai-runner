import unittest
from android_identity_gate import verify

def ui(*texts):
    return ('<hierarchy>'+''.join('<node text="'+t+'" content-desc=""/>' for t in texts)+'</hierarchy>').encode()

class GateTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(verify(ui("@lucasrosalem","Editar perfil","Posts"),"lucasrosalem"),"AUTH_IDENTITY_UI_VERIFIED")
    def test_chooser_not_auth(self):
        with self.assertRaisesRegex(ValueError,"ACCOUNT_HANDLE_NOT_VISIBLE"):
            verify(ui("Continue with Google","Login"),"lucasrosalem")
    def test_handle_alone_not_auth(self):
        with self.assertRaisesRegex(ValueError,"AUTHENTICATED_PROFILE_CONTROL_NOT_VISIBLE"):
            verify(ui("@lucasrosalem","Followers"),"lucasrosalem")
    def test_login_control_rejects(self):
        with self.assertRaisesRegex(ValueError,"LOGIN_CONTROL_VISIBLE"):
            verify(ui("@lucasrosalem","Edit profile","Log in"),"lucasrosalem")
    def test_other_account_rejects(self):
        with self.assertRaisesRegex(ValueError,"ACCOUNT_HANDLE_NOT_VISIBLE"):
            verify(ui("@otheruser","Edit profile"),"lucasrosalem")
    def test_prefix_attack(self):
        with self.assertRaisesRegex(ValueError,"ACCOUNT_HANDLE_NOT_VISIBLE"):
            verify(ui("@lucasrosalem_fake","Edit profile"),"lucasrosalem")
