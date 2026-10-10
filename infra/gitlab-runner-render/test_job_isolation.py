"""Regression tests for the Render GitLab custom executor configuration."""
import json
import os
import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch

DRIVER = pathlib.Path(__file__).with_name("custom_executor.py")

class JobIsolationTests(unittest.TestCase):
    def test_distinct_jobs_have_distinct_roots(self):
        outputs = []
        for job_id in ("12345", "12346"):
            env = {**os.environ, "CUSTOM_ENV_CI_JOB_ID": job_id}
            result = subprocess.run([sys.executable, str(DRIVER), "config"], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads(result.stdout)
            self.assertFalse(config["builds_dir_is_shared"])
            self.assertTrue(config["builds_dir"].endswith("/" + job_id))
            outputs.append(config)
        self.assertNotEqual(outputs[0]["builds_dir"], outputs[1]["builds_dir"])
        self.assertNotEqual(outputs[0]["cache_dir"], outputs[1]["cache_dir"])

    def test_rejects_invalid_job_id(self):
        for value in ("", "../escape", "not-a-number"):
            with self.subTest(value=value):
                env = {**os.environ, "CUSTOM_ENV_CI_JOB_ID": value}
                result = subprocess.run([sys.executable, str(DRIVER), "config"], env=env, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)

if __name__ == "__main__":
    unittest.main()
