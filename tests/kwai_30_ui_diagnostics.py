#!/usr/bin/env python3
"""Thirty independent, synthetic Kwai UI diagnostics; no credentials or screenshots."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from kwai_login_ui_locator import profile_tab, native_chooser_visible, email_form_visible, email_entry, parse
from kwai_ui_safe_diagnose import classify

SCENARIOS = [
 ("resource-profile", "profile", "id_home_bottom_tab_me", "main"),
 ("resource-profile-alt", "", "ll_profile", "main"),
 ("bottom-profile-en", "Profile", "", "main"),
 ("bottom-profile-pt", "Perfil", "", "main"),
 ("bottom-me", "Me", "", "main"),
 ("bottom-eu", "Eu", "", "main"),
 ("top-profile-heading", "Profile", "", "top"),
 ("top-create-profile", "Create your profile", "", "top"),
 ("inbox-only", "Inbox", "", "main"),
 ("discover-only", "Discover", "", "main"),
 ("swipe-tutorial", "Swipe up to watch more", "", "main"),
 ("onboarding-choose", "Choose what you like", "", "main"),
 ("onboarding-like", "Choose like or dislike", "", "main"),
 ("onboarding-better", "Let us know you better", "", "main"),
 ("resource-downloading", "Downloading resources", "", "main"),
 ("resource-download", "Resource download", "", "main"),
 ("permission-allow", "Allow Kwai to send", "", "main"),
 ("permission-deny", "", "permission_deny_button", "main"),
 ("app-error", "App isn't responding", "", "main"),
 ("app-stopping", "App keeps stopping", "", "main"),
 ("native-chooser", "E-mail", "login_platform_expand_text", "main"),
 ("native-chooser-pt", "Correio eletrônico", "login_platform_expand_text", "main"),
 ("native-chooser-no-email", "Google", "login_platform_expand_text", "main"),
 ("email-edit", "Email", "login_email_input", "edit"),
 ("password-edit", "Senha", "login_password_input", "edit"),
 ("phone-edit", "Phone", "login_phone_input", "edit"),
 ("unrelated-edit", "Search", "", "edit"),
 ("tiny-screen-profile", "Profile", "", "tiny"),
 ("bad-bounds-profile", "Profile", "", "invalid"),
 ("resource-profile-top", "Profile", "id_home_bottom_tab_me", "top"),
]
assert len(SCENARIOS) == 30

def main():
    idx=int(sys.argv[1])
    assert 0 <= idx < 30
    name, label, resource, kind=SCENARIOS[idx]
    y1,y2=(40,100) if kind=="top" else (750,850)
    if kind=="tiny": y1,y2=200,280
    bounds="[0,0][0,0]" if kind=="invalid" else f"[20,{y1}][320,{y2}]"
    klass="android.widget.EditText" if kind=="edit" else "android.widget.TextView"
    root=ET.Element("hierarchy")
    ET.SubElement(root,"node",{"text":label,"resource-id":"com.kwai.video:id/"+resource if resource else "", "class":klass,"bounds":bounds})
    xml=ET.tostring(root,encoding="unicode")
    nodes=parse(xml)
    state=classify(xml)
    coords=profile_tab(nodes,xml)
    chooser=native_chooser_visible(nodes,xml)
    form=email_form_visible(nodes)
    expected_profile=idx in (0,1,2,3,4,5,29)
    expected_chooser=idx in (20,21)
    expected_form=idx in (23,24,25)
    assert (coords is not None)==expected_profile,(name,"profile",coords)
    assert chooser==expected_chooser,(name,"chooser",chooser)
    assert form==expected_form,(name,"form",form)
    assert state["dump_valid"] if "dump_valid" in state else True
    assert state["node_count"]==1
    print(json.dumps({"scenario":idx,"name":name,"passed":True,"profile":bool(coords),"chooser":chooser,"form":form},sort_keys=True))
if __name__=="__main__":main()
