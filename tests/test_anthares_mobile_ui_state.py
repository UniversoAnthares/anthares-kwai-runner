import unittest
from anthares_mobile.ui_state import parse

class KwaiUiStateTests(unittest.TestCase):
    def test_create_profile_and_email_action(self):
        xml='''<hierarchy><node text="Create your profile" bounds="[0,0][1080,200]"/><node text="Continue with Google" bounds="[100,700][980,900]"/><node text="Email" bounds="[500,950][1000,1100]"/></hierarchy>'''
        r=parse(xml,'lucasrosalem')
        self.assertEqual(r['state'],'CREATE_PROFILE')
        self.assertFalse(r['identity_verified'])
        self.assertTrue(any(a['action']=='email' for a in r['actions']))
    def test_identity_is_stronger_than_generic_profile(self):
        xml='''<hierarchy><node text="Profile @lucasrosalem Followers 10 Following 2" bounds="[0,0][1080,300]"/></hierarchy>'''
        r=parse(xml,'lucasrosalem')
        self.assertEqual(r['state'],'AUTHENTICATED_PROFILE')
        self.assertTrue(r['identity_verified'])
    def test_generic_profile_not_identity_proof(self):
        xml='''<hierarchy><node text="Profile Followers Following" bounds="[0,0][1080,300]"/></hierarchy>'''
        r=parse(xml,'lucasrosalem')
        self.assertEqual(r['state'],'PROFILE_UNKNOWN')
        self.assertFalse(r['identity_verified'])

    def test_typed_username_on_login_screen_is_not_identity(self):
        xml='''<hierarchy><node class="android.widget.EditText" text="lucasrosalem" bounds="[0,0][100,100]"/><node text="Password" bounds="[0,200][100,300]"/><node text="Profile" bounds="[0,400][100,500]"/></hierarchy>'''
        r=parse(xml,'lucasrosalem')
        self.assertEqual(r['state'],'AUTH_REQUIRED')
        self.assertFalse(r['identity_verified'])
    def test_username_in_feed_not_identity(self):
        xml='''<hierarchy><node text="@lucasrosalem" bounds="[0,0][100,100]"/><node text="For you" bounds="[0,300][100,400]"/></hierarchy>'''
        r=parse(xml,'lucasrosalem')
        self.assertEqual(r['state'],'FEED')
        self.assertFalse(r['identity_verified'])
    def test_profile_username_with_login_prompt_not_identity(self):
        xml='''<hierarchy><node text="Profile @lucasrosalem Followers 10" bounds="[0,0][1080,300]"/><node text="Log in" bounds="[0,400][100,500]"/></hierarchy>'''
        r=parse(xml,'lucasrosalem')
        self.assertEqual(r['state'],'AUTH_REQUIRED')
        self.assertFalse(r['identity_verified'])
    def test_create_profile_with_typed_username_not_identity(self):
        xml='''<hierarchy><node text="Create your profile @lucasrosalem" bounds="[0,0][1080,300]"/></hierarchy>'''
        r=parse(xml,'lucasrosalem')
        self.assertEqual(r['state'],'CREATE_PROFILE')
        self.assertFalse(r['identity_verified'])

if __name__=='__main__':unittest.main()
