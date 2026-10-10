#!/usr/bin/env python3
"""Privacy-safe Android UI classification. Never prints raw labels or identifiers."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kwai_login_ui_locator import profile_tab as profile_coords, bounds as node_bounds

def classify(xml):
    nodes=list(ET.fromstring(xml).iter("node"))
    labels=" ".join(((n.get("text") or "")+" "+(n.get("content-desc") or "")) for n in nodes).lower()
    ids=" ".join(n.get("resource-id") or "" for n in nodes).lower()
    def anyof(*terms): return any(t in labels or t in ids for t in terms)
    screen_height=max((node_bounds(n)[3] for n in nodes if node_bounds(n)),default=0)
    exact_profile=[n for n in nodes if ((n.get("text") or "")+" "+(n.get("content-desc") or "")).strip().casefold() in ("profile","perfil","me","eu")]
    bottom_profile=[n for n in exact_profile if node_bounds(n) and screen_height>=500 and sum(node_bounds(n)[1::2])//2>=screen_height*.76]
    # Aggregate geometry only: no raw UI text, resource identifiers or screenshots.
    profile_hints=[n for n in nodes if "profile" in (n.get("resource-id") or "").casefold()]
    hint_bounded=[n for n in profile_hints if node_bounds(n)]
    bottom_hints=[n for n in hint_bounded if sum(node_bounds(n)[1::2])//2 >= screen_height*.76]
    # An "app info" label is not evidence of a crash.
    system_nodes=[n for n in nodes if (n.get("package") or "").startswith(
        ("com.android.systemui","com.google.android.permissioncontroller","com.android.permissioncontroller"))]
    system_labels=" ".join(((n.get("text") or "")+" "+(n.get("content-desc") or "")) for n in system_nodes).lower()
    crash_phrases=("isn't responding","is not responding","keeps stopping","não está respondendo","continua parando")
    explicit_crash=any(term in system_labels for term in crash_phrases)
    ambiguous_error=any(term in labels for term in crash_phrases) and not explicit_crash
    return {
        "system_error_unattributed":ambiguous_error,
        "system_dialog_node_count":len(system_nodes),
        "profile_hint_bounded_count":len(hint_bounded),
        "profile_hint_bottom_count":len(bottom_hints),
        "profile_hint_unbounded_count":len(profile_hints)-len(hint_bounded),
        "screen_height_bucket":("small" if screen_height < 500 else "normal"),
        "node_count":len(nodes),
        "edittext_count":sum((n.get("class") or "").endswith("EditText") for n in nodes),
        "profile_tab":anyof("id_home_bottom_tab_me","/ll_profile") or profile_coords(nodes,xml) is not None,
        "profile_exact_label_count":len(exact_profile),
        "profile_bottom_label_count":len(bottom_profile),
        "profile_resource_hint_count":sum("profile" in (n.get("resource-id") or "").casefold() for n in nodes),
        "login_chooser":anyof("login_platform_expand_text"),
        "permission_modal":anyof("permission_allow_button","permission_deny_button","allow kwai to send","enviar notificações"),
        "interest_onboarding":anyof("choose like or dislike","let us know you better","choose what you like"),
        "swipe_tutorial":anyof("swipe up to watch more","deslize para cima"),
        "resource_overlay":anyof("resource downloading","downloading resources","resource download"),
        "main_navigation":anyof("id_home_bottom_tab_me","/ll_profile","profile","perfil","inbox","discover"),
        "login_form":anyof("login_email_input","login_password_input","login_phone_input"),
        "verification_challenge":anyof("verification code","verification_code","código de verificação","sms code","otp"),
        "captcha_challenge":anyof("captcha","slide to verify","arraste para verificar","security verification"),
        "phone_login_option":anyof("login_phone","phone number","número de telefone","continue with phone"),
        "google_login_option":anyof("continue with google","login_google","google sign in"),
        "email_login_option":anyof("login_email","continue with email","entrar com e-mail"),
        "system_error":explicit_crash,
    }

def main():
    if len(sys.argv)!=2: return 2
    try:
        with open(sys.argv[1],encoding="utf-8") as f: result=classify(f.read())
    except (OSError, UnicodeError, ET.ParseError):
        print(json.dumps({"dump_valid":False},sort_keys=True)); return 1
    print(json.dumps({"dump_valid":True,**result},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
