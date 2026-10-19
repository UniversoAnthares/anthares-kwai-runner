import datetime as dt
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('admission', Path(__file__).with_name('ssh-admission.py'))
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


class AdmissionTests(unittest.TestCase):
    def test_fresh_heartbeat_is_only_a_skip_hint(self):
        now = dt.datetime(2026, 10, 19, tzinfo=dt.timezone.utc)
        value = {'service': 'anthares-remote-primary', 'state': 'neon',
                 'device_connected': True, 'device_seen_at': now.isoformat()}
        self.assertTrue(admission.recent_device(value, now))
        self.assertFalse(admission.recent_device(value, now + dt.timedelta(seconds=91)))
        self.assertFalse(admission.recent_device(value, now - dt.timedelta(seconds=1)))
        self.assertFalse(admission.recent_device({}, now))
        value['service'] = 'different-service'
        self.assertFalse(admission.recent_device(value, now))

    def test_reruns_reserve_budget_as_separate_private_sessions(self):
        self.assertEqual(admission.attempts([{'run_attempt': 3}, {'run_attempt': 1}]), 4)

    def test_quota_saturation_blocks_before_private_login(self):
        original = admission.github
        admission.github = lambda path: ({'workflow_id': 1} if path.startswith('/actions/runs/')
                                        else {'workflow_runs': [{'run_attempt': 145}]})
        try:
            with self.assertRaisesRegex(RuntimeError, 'quota safety cap'):
                admission.budget()
        finally:
            admission.github = original

    def test_unavailable_usage_history_is_not_assumed_zero(self):
        original = admission.github
        def unavailable(_):
            raise ConnectionError('GitHub unavailable')
        admission.github = unavailable
        try:
            with self.assertRaises(ConnectionError):
                admission.budget()
        finally:
            admission.github = original


if __name__ == '__main__':
    unittest.main()
