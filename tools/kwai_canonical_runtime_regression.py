#!/usr/bin/env python3
"""Offline full-stack regression after reconciling the live Windows Kwai worker.

No network access, Android control, credentials or media files are required.
"""
from __future__ import annotations
import ast
import importlib
import json
import os
import pathlib
import sys
import tempfile
import xml.etree.ElementTree as ET

root=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(root))

def code(name):
    s=(root/name).read_text(encoding='utf8')
    ast.parse(s)
    return s

daemon=code('kwai_physical_queue_daemon.py')
public=code('kwai_physical_public_proof.py')
native=code('kwai_native_cortes.py')
worker=code('kwai_device_failover_worker.py')
client=code('cortes_neon_queue_client.py')
share=code('kwai_phone_share_clipboard.py')

for term in ('def compute_schedule(', 'def sweep_unproven(', 'def acquire_physical_device_lock(',
             'def release_physical_device_lock(', 'def repair_pending(', 'def complete_origin_callback(',
             'KWAI_RECONCILED_WP_SYNC', "if now-prior>=65:", 'KWAI_PROOF_RECOVERY_',
             'kwai-public-post-proportional-06to23-v3', 'def can_attempt_cut('):
    assert term in daemon, 'Windows daemon lost safety guard: '+term
for term in ('KWAI_PUBLIC_PROFILE_INDEX_PENDING_RETRYABLE',
             'KWAI_PUBLIC_MEDIA_MATCH_PENDING_RETRYABLE',
             'KWAI_CAPTIONLESS_STREAM_SCOPE_INVALID','source_media_sha256',
             'source_best_inliers','public_post_timestamp_ms','qualifying_distinct_frames'):
    assert term in public, 'Public proof lost guard: '+term
assert "'unproven':'kwai-unproven'" in client
assert 'KWAI_PHYSICAL_NEON_CANONICAL_URL_REQUIRED' in client
assert "KWAI_UP_STATE=FAILED ERROR=timeout" in worker
assert "KWAI_PHONE_MEDIA_REUSED_VERIFIED_SHA256" in native
print('CANONICAL_MODULES_AND_FAIL_CLOSED_GUARDS_PASS')

# Execute only the isolated scheduler function: no Android, network or file IO.
import datetime
from zoneinfo import ZoneInfo
mod=ast.parse(daemon)
fn_node=next(n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name=='compute_schedule')
scheduler={'EXPECTED_ACCOUNT':'lucasrosalem','load_schedule':lambda:{},
           'save_schedule':lambda value:None}
exec(compile(ast.Module(body=[fn_node],type_ignores=[]),'<kwai-schedule-only>','exec'),scheduler)
fn=scheduler['compute_schedule']
tz=ZoneInfo('America/Campo_Grande')
def local(h,m=0,s=0):
    return datetime.datetime(2026,11,13,h,m,s,tzinfo=tz)
def snapshot(now,status,pending=16,confirmed=0,used=0,first=None,last=None,next_due=None):
    return {'ok':True,'pacing_version':'kwai-public-post-proportional-06to23-v3',
            'target_key':'kwai:lucasrosalem','window_open_at':local(6).isoformat(),
            'deadline_at':local(23).isoformat(),'confirmed_today':confirmed,
            'started_today':used,'remaining_today':min(pending,100-used),
            'first_confirmed_at':first.isoformat() if first else None,
            'last_confirmed_at':last.isoformat() if last else None,
            'next_due_at':next_due.isoformat() if next_due else None,'status':status}
for now,status,next_due in [
    (local(5,59,59),'WAIT_OPEN',local(6)),
    (local(6),'DUE',local(6)),
    (local(23),'BLOCKED_SAME_DAY_CAPACITY',None)
]:
    sec,record=fn(0,16,100,now,snapshot(now,status,next_due=next_due))
    assert record['status']==status,(now,status,record)
first,last=local(6,35),local(15,50)
due=last+(local(23)-last)/17
sec,record=fn(14,16,100,local(18,30),snapshot(
    local(18,30),'DUE',confirmed=14,used=14,first=first,last=last,next_due=due))
assert record['status']=='DUE' and 1500 < sec < 1600,record
try:
    invalid=snapshot(local(5,59,59),'WAIT_OPEN',next_due=local(6))
    invalid['window_open_at']=local(7).isoformat()
    fn(0,16,100,local(5,59,59),invalid)
except RuntimeError as exc:
    assert 'kwai_pacing_open_window_mismatch' in str(exc)
else:
    raise AssertionError('Invalid server opening time was accepted')
print('KWAI_LOCAL_V3_WINDOW_06_23_AND_DUE_MATH_PASS')


# Exercise terminal ACK decision with AST-only isolated code (no filesystem writes).
fn_node=next(n for n in ast.parse(daemon).body
             if isinstance(n,ast.FunctionDef) and n.name=='terminal_ack_decision')
isolated={'EXPECTED_ACCOUNT':'lucasrosalem'}
exec(compile(ast.Module(body=[fn_node],type_ignores=[]),'<kwai-ack-only>','exec'),isolated)
ack_decision=isolated['terminal_ack_decision']
jid='kwai-cortes-A7BsgCe3-oo-g1-A7BsgCe3-oo-7595-7635'
local_row={'state':'quarantined_uncertain','lease_generation':173}
receipt={'ok':True,'id':jid,'target_key':'kwai:lucasrosalem',
         'lease_generation':173,'terminal':'confirmed'}
assert ack_decision(jid,local_row,receipt)=='completed_acknowledged'
assert ack_decision(jid,local_row,{**receipt,'terminal':'cancelled'})=='cancelled_acknowledged'
for fake in [
    {**receipt,'id':'kwai-cortes-other'},
    {**receipt,'target_key':'kwai:universoanthares'},
    {**receipt,'lease_generation':174},
    {**receipt,'terminal':None},
    {**receipt,'ok':False},
    {**receipt,'terminal':'uncertain'}
]:
    assert ack_decision(jid,local_row,fake) is None,fake
isolated['EXPECTED_ACCOUNT']='universoanthares'
jid2='kwai-cortes-ua-217fddfeae7c0a86be66d8e8511e2916'
assert ack_decision(jid2,{'state':'published_pending_ack','lease_generation':1},
    {'ok':True,'id':jid2,'target_key':'kwai:universoanthares',
     'lease_generation':1,'terminal':'confirmed'})=='completed_acknowledged'
assert "'terminal':'kwai-job-terminal-read'" in client
assert "call('terminal',{'id':jid,'lease_generation':int(row.get('lease_generation') or 0)})" in daemon
print('KWAI_TERMINAL_ACK_FAIL_CLOSED_READONLY_PASS')


class ReachedVerifiedShare(Exception):
    pass

for account,app,display in [
    ('lucasrosalem','kwai.lite.video','Lucas Rosalem'),
    ('universoanthares','com.kwai.video','Universo Anthares')
]:
    os.environ['KWAI_EXPECTED_ACCOUNT']=account
    sys.modules.pop('kwai_phone_share_clipboard',None)
    helper=importlib.import_module('kwai_phone_share_clipboard')
    jid='kwai-cortes-test-'+account+'-captionless'
    post='2026-11-12 05:42 PM'
    st={'job_id':jid,'expected_account':account,'state':'verified',
        'publication_attempted':True,'publication_attempted_at':1794519722,
        'caption':'','caption_optional':True,
        'profile_verification':{'account':account,'post_time':post}}
    nodes=ET.fromstring('<hierarchy>'+
       '<node resource-id="'+app+'.basis:id/tv_slide_play_user_name" text="'+display+'" />'+
       '<node resource-id="'+app+'.basis:id/tv_slide_play_post_time" text="'+post+'" />'+
       '<node resource-id="'+app+'.basis:id/forward_button" bounds="[940,1615][1071,1756]" clickable="true"/>'+
       '</hierarchy>')
    with tempfile.TemporaryDirectory(prefix='kwai-share-test-') as tmp:
        target=pathlib.Path(tmp)
        (target/(jid+'.json')).write_text(json.dumps(st),encoding='utf8')
        helper.STATE=target
        helper.adb=lambda *a,**k:helper.DETAIL if a==('shell','dumpsys','window') else ''
        helper.nodes=lambda label:list(nodes.iter('node'))
        taps=[]
        def mock_tap(x,y):
            taps.append((x,y))
            raise ReachedVerifiedShare()
        helper.tap=mock_tap
        try:helper.capture(jid)
        except ReachedVerifiedShare:pass
        else:raise AssertionError('Exact share button never reached')
        assert taps==[(1005,1685)],'Incorrect verified public share target'
        # Normal-caption state must still require the exact public caption.
        st['caption_optional']=False
        (target/(jid+'.json')).write_text(json.dumps(st),encoding='utf8')
        taps.clear()
        try:helper.capture(jid)
        except RuntimeError as exc:
            assert 'KWAI_CAPTION_REQUIRED_DESCRIPTION_MISSING' in str(exc)
        else:raise AssertionError('Missing non-optional caption accepted')
        assert not taps,'Unverified share action attempted'
    print('CAPTIONLESS_AUTHENTICATED_APP_SHARE_GATE_PASS',account)

print('ALL_CANONICAL_WINDOWS_KWAI_REGRESSIONS_PASS')
