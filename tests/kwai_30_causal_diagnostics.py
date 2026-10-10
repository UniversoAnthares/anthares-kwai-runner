#!/usr/bin/env python3
"""Thirty independent causal hypotheses for Kwai Android login failure.
No credentials, real UI, private logs or Android emulator required.
"""
import importlib.util
import json
import pathlib
import sys
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from kwai_android_causal_probe import classify
from kwai_login_ui_locator import parse,profile_tab,email_form_visible,native_chooser_visible

CASES=[
 ("crash","FATAL EXCEPTION: main com.kwai.video","process_crash"),
 ("anr","ANR in com.kwai.video","application_not_responding"),
 ("activity","Unable to start activity com.kwai.video","activity_launch_failure"),
 ("network","ConnectException com.kwai.video","network_failure"),
 ("ssl","SSLHandshakeException com.kwai.video","network_failure"),
 ("dns","UnknownHostException com.kwai.video","network_failure"),
 ("timeout","SocketTimeoutException com.kwai.video","network_failure"),
 ("dead","Process com.kwai.video has died","process_crash"),
 ("signal","Fatal signal 11 com.kwai.video","process_crash"),
 ("permission","Permission Denial start com.kwai.video","activity_launch_failure"),
 ("activity_missing","ActivityNotFoundException com.kwai.video","activity_launch_failure"),
 ("input_timeout","Input dispatching timed out com.kwai.video","application_not_responding"),
 ("unrelated","FATAL EXCEPTION: com.other.app",None),
 ("info","FATAL EXCEPTION: com.kwai.video",None),
 ("debug","ANR in com.kwai.video",None),
 ("other_tag","FATAL EXCEPTION: com.kwai.video",None),
 ("blank","",None),
 ("benign","Starting com.kwai.video",None),
 ("network_info","ConnectException com.kwai.video",None),
 ("repeated","ANR in com.kwai.video","application_not_responding"),
 ("profile_top","profile",None),
 ("profile_bottom","profile","profile"),
 ("profile_rid","user_profile_tab","profile"),
 ("profile_avatar","profile_avatar",None),
 ("profile_heading","create_profile",None),
 ("email_form","email","email_form"),
 ("chooser","Email","chooser"),
 ("empty_ui","",None),
 ("invalid_bounds","profile",None),
 ("system_dialog","permission",None),
]
assert len(CASES)==30

def check(idx):
    name,payload,expected=CASES[idx]
    if idx<20:
        tag="ActivityManager"
        level="E"
        if idx==13 or idx==18:level="I"
        if idx==14:level="D"
        if idx==15:tag="ThirdParty"
        line=f"10-10 20:00:00.000 123 456 {level} {tag}: {payload}"
        report=classify(line)
        got=[k for k,v in report["signals"].items() if v]
        assert (expected in got) if expected else not got,(name,got)
    else:
        if idx==25:
            xml='<hierarchy><node class="android.widget.EditText" resource-id="com.kwai.video:id/login_email_input" bounds="[20,100][300,160]"/></hierarchy>'
        elif idx==26:
            xml='<hierarchy><node class="android.widget.TextView" text="Email" bounds="[20,100][300,160]"/></hierarchy>'
        elif idx==27:
            xml="<hierarchy/>"
        elif idx==29:
            xml='<hierarchy><node class="android.widget.TextView" text="Permission" bounds="[20,100][300,160]"/></hierarchy>'
        else:
            rid=payload if idx in (22,23,24) else ""
            label=payload if idx in (20,21,28) else ""
            y=760 if idx in (21,22,23,24) else 100
            b=f"[200,{y}][300,{y+70}]" if idx!=28 else "invalid"
            xml=f'<hierarchy><node text="{label}" resource-id="com.kwai.video:id/{rid}" bounds="{b}"/><node bounds="[0,0][420,900]"/></hierarchy>'
        nodes=parse(xml)
        if expected=="profile":assert profile_tab(nodes,xml) is not None,name
        elif expected=="email_form":assert email_form_visible(nodes),name
        elif expected=="chooser":assert native_chooser_visible(nodes,xml),name
        else:assert profile_tab(nodes,xml) is None,name
    print("CAUSAL_TEST_PASSED="+str(idx)+";HYPOTHESIS="+name)

if __name__=="__main__":
    check(int(sys.argv[1]))
