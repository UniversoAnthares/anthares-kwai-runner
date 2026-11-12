#!/usr/bin/env python3
"""Strict, device-free Kwai optional notification overlay regression tests."""
from __future__ import annotations
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
import kwai_native_cortes as n
original=(n.dump,n.tap,n.time.sleep,n.ACCOUNT)
try:
 for account,prefix in (('universoanthares','com.kwai.video'),('lucasrosalem','kwai.lite.video')):
  n.ACCOUNT=account
  popup=ET.fromstring(
   '<hierarchy><node resource-id="'+prefix+'.basis:id/tv_dialog_title" text="Ative as notificacoes" />'
   '<node resource-id="'+prefix+':id/iv_close" clickable="true" enabled="true" bounds="[983,788][1038,843]"/></hierarchy>')
  profile=ET.fromstring('<hierarchy><node resource-id="'+prefix+'.basis:id/id_home_bottom_tab_me" clickable="true" enabled="true" bounds="[900,2100][1070,2300]"/></hierarchy>')
  taps=[];calls=[]
  def read(serial,name):
   calls.append(name);return (popup if len(calls)==1 else profile),None
  n.dump=read
  n.tap=lambda serial,node:taps.append(node.attrib.get('resource-id'))
  n.time.sleep=lambda seconds:None
  _,tab,_=n.wait('simulated',n.RID_PROFILE,'known-popup',seconds=3)
  assert taps==[prefix+':id/iv_close'],taps
  assert tab.attrib.get('resource-id')==prefix+'.basis:id/id_home_bottom_tab_me'
  assert len(calls)==2
  print('KWAI_OPTIONAL_NOTIFICATION_'+account.upper()+'_PASS')
 # A guessed/wrong notification title may never authorize an arbitrary close.
 n.ACCOUNT='universoanthares';wrong=ET.fromstring(
  '<hierarchy><node resource-id="com.kwai.video.basis:id/tv_dialog_title" text="Security approval required"/>'
  '<node resource-id="com.kwai.video:id/iv_close" clickable="true" enabled="true" bounds="[983,788][1038,843]"/></hierarchy>')
 taps=[]
 def read_wrong(serial,name):
  if taps:raise AssertionError('unauthorized UI close')
  if not getattr(read_wrong,'called',False):
   return first()
  raise n.E('UNKNOWN_SECURITY_PROMPT_MUST_REMAIN_OPEN')
 def first():
  read_wrong.called=True
  return wrong,None
 read_wrong.called=False
 n.dump=read_wrong;n.tap=lambda serial,node:taps.append(node)
 try:n.wait('simulated',n.RID_PROFILE,'security-prompt',seconds=3)
 except n.E as exc:assert 'UNKNOWN_SECURITY_PROMPT_MUST_REMAIN_OPEN' in str(exc)
 else:raise AssertionError('wrong prompt unexpectedly passed')
 assert not taps
 print('KWAI_UNKNOWN_PROMPT_FAIL_CLOSED_PASS')
finally:
 n.dump,n.tap,n.time.sleep,n.ACCOUNT=original
