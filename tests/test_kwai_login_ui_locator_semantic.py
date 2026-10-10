import unittest
from tools.kwai_login_ui_locator import parse,email_entry,google_entry,native_chooser_visible

class SemanticLocatorFallbackTests(unittest.TestCase):
    XML='''<hierarchy><node text="Create your profile" bounds="[0,0][1080,220]"/><node text="Continue with Google" bounds="[120,700][960,900]"/><node text="Email" bounds="[600,950][980,1100]"/></hierarchy>'''
    def test_native_chooser_detected_without_resource_ids(self):
        nodes=parse(self.XML)
        self.assertTrue(native_chooser_visible(nodes,self.XML))
    def test_email_fallback_coordinates(self):
        nodes=parse(self.XML)
        self.assertEqual(email_entry(nodes,self.XML),(790,1025))
    def test_google_fallback_coordinates(self):
        nodes=parse(self.XML)
        self.assertEqual(google_entry(nodes,self.XML),(540,800))

if __name__=='__main__':unittest.main()
