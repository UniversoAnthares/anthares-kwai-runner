import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'direct-tiktok-publisher'))

from tiktok_publish_adapter import AdapterSpecError, TikTokPublishSpec


class TikTokPublishAdapterTests(unittest.TestCase):
    def base(self):
        return {
            'account': '@universo.anthares',
            'source_id': '9CIk-I_3VhM',
            'source_start': 8,
            'source_end': 98,
            'media_sha256': 'a' * 64,
            'media_path': '/tmp/video.mp4',
            'destination': 'tiktok',
            'source_url': 'https://www.youtube.com/watch?v=9CIk-I_3VhM',
            'title': 'Trecho',
            'summary': 'Resumo',
        }

    def test_normalizes_and_parameterizes_all_identity_fields(self):
        spec = TikTokPublishSpec.from_mapping(self.base())
        self.assertEqual(spec.account, 'universo.anthares')
        self.assertEqual(spec.segment_id, '9CIk-I_3VhM:8:98')
        self.assertIn('universo.anthares', spec.dedupe_key)
        self.assertIn('tiktok', spec.dedupe_key)
        self.assertEqual(spec.job_payload()['source_start'], 8.0)
        self.assertEqual(spec.plan_payload()['destination'], 'tiktok')

    def test_dedupe_changes_if_hash_changes(self):
        a = TikTokPublishSpec.from_mapping(self.base())
        raw = self.base(); raw['media_sha256'] = 'b' * 64
        b = TikTokPublishSpec.from_mapping(raw)
        self.assertNotEqual(a.dedupe_key, b.dedupe_key)
        self.assertNotEqual(a.job_id, b.job_id)

    def test_rejects_bad_interval_hash_destination_and_account(self):
        cases = []
        x = self.base(); x['source_end'] = 8; cases.append(x)
        x = self.base(); x['media_sha256'] = 'bad'; cases.append(x)
        x = self.base(); x['destination'] = 'kwai'; cases.append(x)
        x = self.base(); x['account'] = '@'; cases.append(x)
        for raw in cases:
            with self.subTest(raw=raw):
                with self.assertRaises(AdapterSpecError):
                    TikTokPublishSpec.from_mapping(raw)

    def test_verify_media_checks_exact_sha(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'v.mp4'
            p.write_bytes(b'anthares-video')
            raw = self.base()
            raw['media_path'] = str(p)
            raw['media_sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
            spec = TikTokPublishSpec.from_mapping(raw)
            spec.verify_media()
            p.write_bytes(b'changed')
            with self.assertRaises(AdapterSpecError):
                spec.verify_media()

    def test_manifest_is_stable_and_complete(self):
        raw = self.base(); raw['logical_id'] = 'fixed-job'
        spec = TikTokPublishSpec.from_mapping(raw)
        manifest = spec.manifest()
        self.assertEqual(manifest['schema'], 'anthares.tiktok.publish-adapter.v1')
        self.assertEqual(manifest['job_id'], 'fixed-job')
        self.assertEqual(manifest['job']['dedupe_key'], manifest['dedupe_key'])
        self.assertEqual(manifest['plan']['source_id'], '9CIk-I_3VhM')


if __name__ == '__main__':
    unittest.main()
