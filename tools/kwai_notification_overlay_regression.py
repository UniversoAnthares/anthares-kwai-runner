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
 # Retain the pre-existing Windows creator-level popup guard after code sync.
 n.ACCOUNT='universoanthares'
 creator=ET.fromstring('<hierarchy>'
  '<node resource-id="com.kwai.video.basis_extension:id/create_user_text" text="Universo Anthares" />'
  '<node resource-id="com.kwai.video.basis_extension:id/create_cancel_button" text="Fechar" clickable="true" enabled="true" bounds="[905,532][977,604]"/>'
  '</hierarchy>')
 ready=ET.fromstring('<hierarchy><node resource-id="com.kwai.video.basis:id/id_home_bottom_tab_me" clickable="true" enabled="true" bounds="[900,2100][1070,2300]"/></hierarchy>')
 taps=[];reads=[]
 def creator_read(serial,name):
  reads.append(name)
  return (creator if len(reads)==1 else ready),None
 n.dump=creator_read;n.tap=lambda serial,node:taps.append(node.attrib.get('resource-id'))
 _,tab,_=n.wait('simulated',n.RID_PROFILE,'creator-guard',seconds=3)
 assert taps==['com.kwai.video.basis_extension:id/create_cancel_button']
 assert tab.attrib.get('resource-id')=='com.kwai.video.basis:id/id_home_bottom_tab_me'
 for invalid in [
  '<hierarchy><node resource-id="com.kwai.video.basis_extension:id/create_user_text" text="Other account"/><node resource-id="com.kwai.video.basis_extension:id/create_cancel_button" text="Fechar" clickable="true" enabled="true" bounds="[905,532][977,604]"/></hierarchy>',
  '<hierarchy><node resource-id="com.kwai.video.basis_extension:id/create_user_text" text="Universo Anthares"/><node resource-id="com.kwai.video.basis_extension:id/create_cancel_button" text="Fechar" clickable="false" enabled="true" bounds="[905,532][977,604]"/></hierarchy>',
 ]:
  bad=ET.fromstring(invalid);taps=[];reads=[]
  def creator_wrong(serial,name):
   reads.append(name)
   if len(reads)==1:return bad,None
   raise n.E('CREATOR_UNKNOWN_PROMPT_PRESERVED')
  n.dump=creator_wrong;n.tap=lambda serial,node:taps.append(node)
  try:n.wait('simulated',n.RID_PROFILE,'creator-invalid',seconds=3)
  except n.E as exc:assert 'CREATOR_UNKNOWN_PROMPT_PRESERVED' in str(exc)
  else:raise AssertionError('Creator prompt accepted unexpectedly')
  assert not taps
 print('KWAI_CREATOR_LEVEL_POPUP_GUARD_PASS')
 # Real secondary popup geometry was observed in the pre-publication UI dump.
 # Whitelist only an exact three-ID optional promotion, then re-read the profile.
 n.ACCOUNT='universoanthares'
 promo=ET.fromstring('<hierarchy>'
  '<node resource-id="com.kwai.video.basis:id/view_content" bounds="[80,532][997,1596]" />'
  '<node resource-id="com.kwai.video:id/colored_button_bg" clickable="true" bounds="[216,1401][861,1533]" />'
  '<node resource-id="com.kwai.video:id/close_button" clickable="true" enabled="true" bounds="[905,532][977,604]"/>'
  '</hierarchy>')
 secondary_profile=ET.fromstring('<hierarchy><node resource-id="com.kwai.video.basis:id/id_home_bottom_tab_me" clickable="true" enabled="true" bounds="[900,2100][1070,2300]"/></hierarchy>')
 taps=[];reads=[]
 def read_promo(serial,name):
  reads.append(name)
  return (promo if len(reads)==1 else secondary_profile),None
 n.dump=read_promo;n.tap=lambda serial,node:taps.append(node.attrib.get('resource-id'))
 _,tab,_=n.wait('simulated',n.RID_PROFILE,'promo-recovered',seconds=3)
 assert taps==['com.kwai.video:id/close_button'],taps
 assert tab.attrib.get('resource-id')=='com.kwai.video.basis:id/id_home_bottom_tab_me'
 assert len(reads)==2
 print('KWAI_SECONDARY_EXACT_PROMO_DISMISS_PASS')
 # A similarly named security popup, incomplete IDs or disabled close fail closed.
 for invalid in [
  '<hierarchy><node resource-id="com.kwai.video:id/close_button" clickable="true" enabled="true" bounds="[905,532][977,604]"/></hierarchy>',
  '<hierarchy><node resource-id="com.kwai.video.basis:id/view_content"/><node resource-id="com.kwai.video:id/colored_button_bg"/><node resource-id="com.kwai.video:id/close_button" clickable="false" enabled="true" bounds="[905,532][977,604]"/></hierarchy>',
  '<hierarchy><node resource-id="com.kwai.video.basis:id/view_content"/><node resource-id="com.kwai.video:id/colored_button_bg"/><node resource-id="com.kwai.video:id/close_button" clickable="true" enabled="false" bounds="[905,532][977,604]"/></hierarchy>',
 ]:
  bad=ET.fromstring(invalid)
  taps=[];reads=[]
  def read_invalid(serial,name):
   reads.append(name)
   if len(reads)==1:return bad,None
   raise n.E('UNKNOWN_PROMPT_PRESERVED')
  n.dump=read_invalid;n.tap=lambda serial,node:taps.append(node)
  try:n.wait('simulated',n.RID_PROFILE,'invalid-promo',seconds=3)
  except n.E as exc:assert 'UNKNOWN_PROMPT_PRESERVED' in str(exc)
  else:raise AssertionError('Untrusted popup accepted')
  assert not taps
 print('KWAI_SECONDARY_PROMO_INVALID_NO_TAP_PASS')
 # The secondary editor displays a clickable Next parent, and a nonclickable
 # Próximo child. Another button directly publishes: never select that one.
 n.ACCOUNT='universoanthares'
 next_parent=ET.fromstring('<hierarchy>'
  '<node resource-id="com.kwai.video.ca_product:id/next_step_button_container">'
  '<node resource-id="com.kwai.video.ca_product:id/edit_post_button" clickable="true" enabled="true" bounds="[50,2052][524,2134]"><node resource-id="com.kwai.video.ca_product:id/post_button_normal" text="Publicar" /></node>'
  '<node resource-id="com.kwai.video.ca_product:id/edit_next_button" clickable="true" enabled="true" bounds="[555,2052][1029,2134]"><node resource-id="com.kwai.video.ca_product:id/next_button_normal" text="Próximo" clickable="false" enabled="true" bounds="[703,2052][880,2134]"/></node>'
  '</node></hierarchy>')
 n.dump=lambda serial,name:(next_parent,None)
 _,selected,_=n.wait('simulated',n.RID_NEXT,'next-parent',seconds=2)
 assert selected.attrib.get('resource-id')=='com.kwai.video.ca_product:id/edit_next_button'
 assert n.center(selected.attrib['bounds'])==(792,2093)
 print('KWAI_SECONDARY_EDITOR_CLICKABLE_NEXT_PARENT_PASS')
 for mod in ('clickable="false" enabled="true" bounds="[555,2052][1029,2134]','clickable="true" enabled="false" bounds="[555,2052][1029,2134]'):
  bad=ET.fromstring(ET.tostring(next_parent,encoding='unicode').replace('clickable="true" enabled="true" bounds="[555,2052][1029,2134]',mod))
  # Force the first read to be invalid; subsequent reads raise so the test is bounded.
  calls=[]
  def reject_next(serial,name):
   calls.append(name)
   if len(calls)==1:return bad,None
   raise n.E('BAD_NEXT_REJECTED')
  n.dump=reject_next
  try:n.wait('simulated',n.RID_NEXT,'next-invalid',seconds=2)
  except n.E as exc:assert 'BAD_NEXT_REJECTED' in str(exc)
  else:raise AssertionError('disabled next was accepted')
 print('KWAI_SECONDARY_EDITOR_DISABLED_NEXT_FAIL_CLOSED_PASS')
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
