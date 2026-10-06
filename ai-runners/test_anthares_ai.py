#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import anthares_ai


class FakeCompleted:
    def __init__(self, payload, returncode=0):
        self.stdout = json.dumps(payload, ensure_ascii=False) + "\n"
        self.stderr = ""
        self.returncode = returncode


class AntharesAITests(unittest.TestCase):
    def test_parse_order_deduplicates(self):
        self.assertEqual(
            anthares_ai.parse_order("grok,claude,grok,gemini"),
            ["grok", "claude", "gemini"],
        )

    def test_strip_envelope(self):
        text = "x START\nresposta útil\nEND y"
        self.assertEqual(anthares_ai.strip_envelope(text, "START", "END"), "resposta útil")

    @patch("anthares_ai.subprocess.run")
    def test_auto_fallback_after_simulated_primary_failure(self, run):
        # The first provider is simulated and never spawns a subprocess; the second succeeds.
        def fake(cmd, **kwargs):
            start = cmd[cmd.index("--expect") + 1]
            end = cmd[cmd.index("--expect-end") + 1]
            return FakeCompleted({
                "provider": "grok",
                "ok": True,
                "status": "SUCCESS",
                "response": "resposta do grok",
                "elapsed_s": 1.0,
                "marker_count": 2,
                "end_marker_count": 2,
            })
        run.side_effect = fake
        with tempfile.TemporaryDirectory() as td:
            result = anthares_ai.execute(
                "teste",
                provider="auto",
                order=["claude", "grok"],
                simulate_failures={"claude"},
                log_path=Path(td) / "log.jsonl",
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "grok")
        self.assertEqual(result["attempts"][0]["status"], "SIMULATED_FAILURE")
        self.assertEqual(result["attempts"][1]["provider"], "grok")

    @patch("anthares_ai.subprocess.run")
    def test_retry_retryable_then_success(self, run):
        calls = {"n": 0}
        def fake(cmd, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return FakeCompleted({"provider": "grok", "ok": False, "status": "CDP_NOT_READY", "response": "", "elapsed_s": 1.0})
            return FakeCompleted({"provider": "grok", "ok": True, "status": "SUCCESS", "response": "ok", "elapsed_s": 1.0})
        run.side_effect = fake
        with tempfile.TemporaryDirectory() as td:
            result, attempts = anthares_ai.run_with_retry(
                "grok", "raw", 30, 30, 1, False, False, Path(td) / "log.jsonl"
            )
        self.assertTrue(result["ok"])
        self.assertEqual(len(attempts), 2)

    @patch("anthares_ai.subprocess.run")
    def test_non_retryable_login_required_stops(self, run):
        run.return_value = FakeCompleted({
            "provider": "manus", "ok": False, "status": "LOGIN_REQUIRED",
            "response": "", "elapsed_s": 1.0,
        })
        with tempfile.TemporaryDirectory() as td:
            result, attempts = anthares_ai.run_with_retry(
                "manus", "raw", 30, 30, 3, False, False, Path(td) / "log.jsonl"
            )
        self.assertFalse(result["ok"])
        self.assertEqual(len(attempts), 1)

    def test_log_never_contains_prompt_or_response(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "log.jsonl"
            anthares_ai.append_log(p, {
                "provider": "claude", "status": "SUCCESS", "ok": True,
                "elapsed_s": 1, "attempt": 1, "prompt_hash": "abc",
                "mode": "local-web", "prompt": "SEGREDO", "response": "RESPOSTA",
            })
            data = p.read_text(encoding="utf-8")
        self.assertNotIn("SEGREDO", data)
        self.assertNotIn("RESPOSTA", data)
        self.assertIn("abc", data)

    @patch("anthares_ai.execute")
    def test_health_requires_expected_marker(self, execute):
        execute.side_effect = lambda prompt, provider, **kwargs: {
            "ok": True, "provider": provider, "status": "SUCCESS",
            "response": prompt.split()[-1], "runtime": "local-web", "attempts": [],
        }
        with tempfile.TemporaryDirectory() as td:
            result = anthares_ai.health(
                "auto", ["claude", "grok"], 30, 30, Path(td) / "log.jsonl"
            )
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["providers"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
