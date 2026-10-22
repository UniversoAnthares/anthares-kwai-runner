import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NightlyWatchdog(unittest.TestCase):
    def test_task_starts_hidden_and_recovers_on_schedule(self):
        text=(ROOT/"tools"/"install_pinterest_night_watchdog.ps1").read_text()
        for expected in ("WindowStyle Hidden","Minutes 10","WakeToRun","StartWhenAvailable","IgnoreNew"):
            self.assertIn(expected,text)
    def test_does_not_touch_personal_browser_and_not_restart_on_rejection(self):
        script=(ROOT/"tools"/"cortes_pinterest_night_watchdog.ps1").read_text()
        self.assertIn("http://127.0.0.1:9226/json/version",script)
        self.assertIn("$lag -gt 22",script)
        self.assertNotIn("Stop-Process",script)
        self.assertNotIn("chrome://",script)
        self.assertNotIn("PIN_PUBLISH_BUTTON_NOT_READY",script)
    def test_watchdog_reports_actual_publish_health(self):
        script=(ROOT/"tools"/"cortes_pinterest_night_watchdog.ps1").read_text()
        self.assertIn("BLOCKED_DRAFT_CAPACITY",script)
        self.assertIn("DEGRADED_SCHEDULED_NOT_PUBLISHING",script)
        self.assertIn("PINTEREST_QUEUE_STALLED",script)
        self.assertIn("PINTEREST_DRAFT_CAPACITY_EXHAUSTED",script)
        self.assertIn("lastConfirmedAt",script)
        self.assertIn("br-crimson-unit-b89nau08-cortesqueue.compute.",script)

    def test_existing_publisher_is_source_of_truth(self):
        script=(ROOT/"tools"/"cortes_pinterest_night_watchdog.ps1").read_text()
        self.assertIn("CORTES-Pinterest-Local",script)
        self.assertIn("Enable-ScheduledTask",script)
        self.assertIn("pinterest-watchdog-health.json",script)
if __name__=="__main__": unittest.main()
