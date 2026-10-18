"""SYSTEM CORTES consumer and one-shot share exclusive singleton fencing."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import kwai_physical_queue_daemon as daemon


class CortesSingletonTests(unittest.TestCase):
    def test_maintenance_blocks_work_before_device_or_queue_use(self):
        with patch.object(daemon.MAINTENANCE,"exists",return_value=True), \
             patch.object(daemon,"repair_pending") as repair, \
             patch.object(daemon,"signed_post") as queue, \
             patch.object(daemon,"preflight") as device, \
             patch.object(daemon,"log"):
            self.assertEqual(daemon.once(),0)
            repair.assert_not_called()
            device.assert_not_called()
            queue.assert_not_called()

    def test_one_shot_obtains_same_lock_as_daemon(self):
        with patch.object(daemon,"lock",return_value=100) as lock, \
             patch.object(daemon,"once",return_value=0) as once, \
             patch.object(daemon.os,"close") as close, \
             patch.object(daemon.LOCK,"unlink") as unlink:
            self.assertEqual(daemon.single_run(),0)
            lock.assert_called_once()
            once.assert_called_once()
            close.assert_called_once_with(100)
            unlink.assert_called_once_with(missing_ok=True)


if __name__=="__main__":
    unittest.main()
