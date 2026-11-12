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
             'KWAI_PACING_VERSION', 'def can_attempt_cut('):
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
