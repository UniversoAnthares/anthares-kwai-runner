import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import kwai_physical_queue_daemon as daemon


class CallbackRecoveryTests(unittest.TestCase):
    def test_storage_quota_uses_backoff_instead_of_publication(self):
        with self.assertRaises(daemon.QueueStorageBlocked):
            daemon.queue_failure('lease',503,{'error':'queue_storage_quota_exhausted'})
    def test_wordpress_failure_is_durable_and_retry_never_publishes(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(daemon, 'WP_PENDING', Path(directory)/'pending.json'), patch.object(daemon, 'log'):
            job={'id':'clip-1','cortes_callback_token':'local-only-token'}
            with patch.object(daemon, 'wp_notify', side_effect=TimeoutError):
                self.assertFalse(daemon.notify_completed(job,'remote-proof'))
            self.assertIn('clip-1', daemon.pending_callbacks())
            with patch.object(daemon, 'wp_notify') as notify, patch.object(daemon, 'process') as publish:
                daemon.repair_wp_callbacks()
                notify.assert_called_once_with(job,'completed','remote-proof')
                publish.assert_not_called()
            self.assertEqual(daemon.pending_callbacks(), {})

    def test_corrupt_retry_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'pending.json';path.write_text('{broken')
            with patch.object(daemon, 'WP_PENDING', path):
                with self.assertRaises(ValueError): daemon.pending_callbacks()
