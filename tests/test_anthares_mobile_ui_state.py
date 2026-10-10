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

if __name__=='__main__':unittest.main()
