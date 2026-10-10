import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from kwai_login_ui_locator import profile_tab

def xml(label="",rid="",y=750,clickable="true",klass="android.widget.TextView"):
    root=ET.Element("hierarchy")
    ET.SubElement(root,"node",{"text":label,"resource-id":"com.kwai.video:id/"+rid,
       "bounds":f"[200,{y}][300,{y+70}]","clickable":clickable,"class":klass})
    ET.SubElement(root,"node",{"text":"","bounds":"[0,0][420,900]"})
    return ET.tostring(root,encoding="unicode")

class ProfileNavigation(unittest.TestCase):
    def test_explicit_bottom(self):
        s=xml(rid="ll_profile"); self.assertEqual(profile_tab(list(ET.fromstring(s).iter("node")),s),(250,785))
    def test_resource_profile_bottom(self):
        s=xml(rid="user_profile_tab"); self.assertEqual(profile_tab(list(ET.fromstring(s).iter("node")),s),(250,785))
    def test_heading_not_tapped(self):
        s=xml(label="Profile",y=50); self.assertIsNone(profile_tab(list(ET.fromstring(s).iter("node")),s))
    def test_avatar_not_tapped(self):
        s=xml(rid="profile_avatar"); self.assertIsNone(profile_tab(list(ET.fromstring(s).iter("node")),s))
    def test_create_profile_not_tapped(self):
        s=xml(rid="create_profile"); self.assertIsNone(profile_tab(list(ET.fromstring(s).iter("node")),s))
    def test_email_field_not_tapped(self):
        s=xml(label="Email",rid="login_email_input",klass="android.widget.EditText"); self.assertIsNone(profile_tab(list(ET.fromstring(s).iter("node")),s))
    def test_nonprofile_not_tapped(self):
        s=xml(label="Inbox",rid="ll_inbox"); self.assertIsNone(profile_tab(list(ET.fromstring(s).iter("node")),s))
    def test_small_screen_rejected(self):
        s='<hierarchy><node text="Profile" bounds="[10,100][90,150]"/></hierarchy>'
        self.assertIsNone(profile_tab(list(ET.fromstring(s).iter("node")),s))
if __name__=="__main__":unittest.main()
