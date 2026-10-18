#!/usr/bin/env python3
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
import cortes_neon_queue_adapter as adapter


class TestNeonAdapter(unittest.TestCase):
    def test_lease_preserves_callback_and_owner(self):
        row={'id':'job-1','lease_generation':2,'lease_owner':'physical_android:DESKTOP-FTDK0HP',
             'target_key':'kwai:lucasrosalem','payload':{'source_id':'live','video_url':'https://anthares.us/clip.mp4',
             'cortes_callback_token':'opaque'}}
        with mock.patch.object(adapter,'call',return_value={'ok':True,'job':row}) as api:
            status,response=adapter.signed_legacy_queue_call('/job/lease',
                {'executor':'physical_android','platform':'kwai','ttl_seconds':3600})
        self.assertEqual(status,200)
        self.assertEqual(response['job']['cortes_callback_token'],'opaque')
        self.assertEqual(response['job']['lease_owner'],adapter.OWNER)
        self.assertEqual(api.call_args.args[0],'lease')
        self.assertEqual(api.call_args.args[1]['lease_seconds'],3600)

    def test_started_is_fenced(self):
        with mock.patch.dict(os.environ, {'KWAI_LEASE_OWNER':'physical_android:DESKTOP-FTDK0HP'}):
            with mock.patch.object(adapter,'call',return_value={'ok':True}) as api:
                status,_=adapter.signed_legacy_queue_call('/job/started',{'id':'a','lease_generation':4})
        self.assertEqual(status,200)
        self.assertEqual(api.call_args.args[1]['lease_generation'],4)

    def test_confirmation_requires_verified_evidence(self):
        with mock.patch.object(adapter,'call') as api:
            status,resp=adapter.signed_legacy_queue_call('/job/complete',{'id':'a','lease_generation':4,
                                                                            'confirmed':True,'remote_id':'r1'})
        self.assertEqual(status,409)
        self.assertFalse(resp['ok'])
        api.assert_not_called()

    def test_confirmation_uses_neon(self):
        with mock.patch.object(adapter,'call',return_value={'ok':True}) as api:
            status,_=adapter.signed_legacy_queue_call('/job/complete',
                {'id':'a','lease_generation':4,'confirmed':True,'remote_id':'r1',
                 'confirmation_evidence':'{"kind":"kwai-profile","account":"lucasrosalem"}'})
        self.assertEqual(status,200)
        self.assertEqual(api.call_args.args[0],'confirm')
        self.assertEqual(api.call_args.args[1]['confirmation_evidence']['account'],'lucasrosalem')

    def test_no_legacy_fallback_on_neon_failure(self):
        with mock.patch.object(adapter,'call',side_effect=ConnectionError('network')):
            status,r=adapter.signed_legacy_queue_call('/job/lease',
                {'executor':'physical_android','platform':'kwai','ttl_seconds':3600})
        self.assertEqual(status,503)
        self.assertEqual(r['error'],'neon_transport_unavailable')
        self.assertFalse(r['publication_allowed'])

    def test_reject_wrong_target(self):
        with mock.patch.object(adapter,'call',return_value={'ok':True,'job':{'target_key':'kwai:other','payload':{}}}):
            status,r=adapter.signed_legacy_queue_call('/job/lease',
                {'executor':'physical_android','platform':'kwai'})
        self.assertEqual(status,409)
        self.assertEqual(r['error'],'unexpected_queue_job_shape')


if __name__=='__main__':
    unittest.main()
