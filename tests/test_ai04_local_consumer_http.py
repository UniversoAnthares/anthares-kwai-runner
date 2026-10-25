"""AI-04 integration: real TCP/HTTP failures against an actual Anthares local consumer.

The HTTP servers are disposable 127.0.0.1 fixtures; no external provider,
quota, billing, social account, browser session or production queue is called.
"""
import json
import socket
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-runners"))
import anthares_ai
from ai_hub.eligibility_breaker import CircuitBreaker, ProviderPolicy


def cfg(name, *, tasks=("text",), authorized=True, credential=True,
        quota=True, budget=True, paid=False, approved=False):
    return ProviderPolicy(name, frozenset(tasks), authorized,
                          credential, quota, budget, paid, approved)


class LocalHttpFixture(BaseHTTPRequestHandler):
    def do_GET(self):
        name = self.path.lstrip("/")
        with self.server.test_lock:
            self.server.counter[name] = self.server.counter.get(name, 0) + 1
            row = self.server.provider_behavior.get(name, {"status": 503})
        if row.get("delay", 0):
            time.sleep(row["delay"])
        status = row.get("status", 200)
        data = json.dumps({"response": "QA_LOCAL_TEXT_" + name}).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


class ActualLocalConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), LocalHttpFixture)
        cls.server.provider_behavior = {}
        cls.server.counter = {}
        cls.server.test_lock = threading.Lock()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        with self.server.test_lock:
            self.server.counter = {}
            self.server.provider_behavior = {}
        self.tmp = tempfile.TemporaryDirectory(prefix="ai04-consumer-http-")
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / "result.jsonl"
        self.now = [100.0]
        self.breaker = CircuitBreaker(clock=lambda: self.now[0], server_fail_threshold=2)

    def http_run_once(self, name, prompt, timeout, response_timeout, envelope, simulate_failure):
        assert not simulate_failure
        assert prompt == "QA_SAFE_PROMPT"
        try:
            with urlopen(self.base + "/" + name, timeout=0.04) as response:
                data = json.loads(response.read().decode())
                return {"provider": name, "ok": True, "status": "SUCCESS",
                        "response": data["response"]}
        except HTTPError as e:
            return {"provider": name, "ok": False, "status": f"HTTP_{e.code}",
                    "http_status": e.code, "response": ""}
        except (TimeoutError, socket.timeout, URLError):
            return {"provider": name, "ok": False, "status": "RESPONSE_TIMEOUT",
                    "response": ""}

    def run_with(self, policies, *, provider="auto", order=None, breaker=None):
        with patch.object(anthares_ai, "run_once", side_effect=self.http_run_once):
            return anthares_ai.execute(
                "QA_SAFE_PROMPT", provider=provider,
                order=order or ["claude", "grok", "gemini", "perplexity", "manus"],
                retries=10,  # this legacy knob MUST be bypassed by AI-04
                log_path=self.log, eligibility_policies=policies,
                eligibility_breaker=breaker or self.breaker,
                timeout=5, response_timeout=5)

    def count(self, name):
        with self.server.test_lock:
            return self.server.counter.get(name, 0)

    def behavior(self, **rows):
        with self.server.test_lock:
            self.server.provider_behavior.update(rows)

    def test_real_http_429_uses_only_verified_eligible_fallback(self):
        self.behavior(claude={"status": 429}, grok={"status": 200})
        result = self.run_with([cfg("claude"), cfg("grok")])
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"], "grok")
        self.assertEqual([x["provider"] for x in result["attempts"]], ["claude","grok"])
        self.assertEqual((self.count("claude"), self.count("grok")), (1,1))
        self.assertTrue(self.breaker.status("claude")["open"])

    def test_second_request_does_not_retry_real_429_provider(self):
        self.behavior(claude={"status": 429}, grok={"status": 200})
        policies=[cfg("claude"), cfg("grok")]
        self.run_with(policies)
        self.run_with(policies)
        self.assertEqual((self.count("claude"), self.count("grok")), (1,2))

    def test_http_402_never_calls_unapproved_paid_fallback(self):
        self.behavior(claude={"status": 402}, grok={"status": 200})
        res=self.run_with([cfg("claude"), cfg("grok",paid=True,approved=False)])
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"],"NO_VERIFIED_UPSTREAM_RESPONSE")
        self.assertEqual((self.count("claude"),self.count("grok")),(1,0))
        self.assertTrue(self.breaker.status("claude")["open"])

    def test_real_socket_timeout_routes_only_one_call_to_next_eligible(self):
        self.behavior(claude={"status":200,"delay":0.18},grok={"status":200})
        res=self.run_with([cfg("claude"),cfg("grok")])
        self.assertTrue(res["ok"])
        self.assertEqual(res["provider"],"grok")
        self.assertEqual((self.count("claude"),self.count("grok")),(1,1))

    def test_quota_unverified_provider_never_called(self):
        self.behavior(claude={"status":200},grok={"status":200})
        res=self.run_with([cfg("claude",quota=False),cfg("grok")])
        self.assertEqual(res["provider"],"grok")
        self.assertEqual((self.count("claude"),self.count("grok")),(0,1))

    def test_no_authorized_eligible_provider_fails_closed_without_network(self):
        res=self.run_with([cfg("claude",credential=False),cfg("grok",authorized=False)])
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"],"NO_ELIGIBLE_VERIFIED_PROVIDER")
        self.assertEqual(self.count("claude")+self.count("grok"),0)

    def test_real_http_403_denies_all_fallback(self):
        self.behavior(claude={"status":403},grok={"status":200})
        res=self.run_with([cfg("claude"),cfg("grok")])
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"],"UPSTREAM_REJECTED")
        self.assertEqual((self.count("claude"),self.count("grok")),(1,0))

    def test_stt_only_capability_cannot_serve_text(self):
        res=self.run_with([cfg("claude",tasks=("stt",))])
        self.assertFalse(res["ok"])
        self.assertEqual(self.count("claude"),0)

    def test_explicit_provider_does_not_fanout_to_others(self):
        self.behavior(claude={"status":200},grok={"status":200})
        res=self.run_with([cfg("claude"),cfg("grok")],provider="grok")
        self.assertEqual(res["provider"],"grok")
        self.assertEqual((self.count("claude"),self.count("grok")),(0,1))

    def test_no_policy_preserves_existing_legacy_consumer_flow(self):
        with patch.object(anthares_ai,"run_once",return_value={
                "provider":"claude","ok":True,"status":"SUCCESS",
                "response":"QA_LEGACY_OK","elapsed_s":0.01}):
            result=anthares_ai.execute(
                "QA_SAFE_PROMPT",provider="claude",retries=0,log_path=self.log)
        self.assertTrue(result["ok"])
        self.assertEqual(result["response"],"QA_LEGACY_OK")
        self.assertEqual(result["status"],"SUCCESS")

    def test_logged_event_does_not_contain_original_prompt_or_token_values(self):
        self.behavior(claude={"status":429},grok={"status":200})
        self.run_with([cfg("claude"),cfg("grok")])
        logs=self.log.read_text(encoding="utf-8")
        self.assertNotIn("QA_SAFE_PROMPT",logs)
        self.assertNotIn("Authorization",logs)
        self.assertEqual(len(logs.strip().splitlines()),2)

    def test_http_503_opens_after_threshold_and_no_infinite_retry(self):
        self.behavior(claude={"status":503})
        policies=[cfg("claude")]
        first=self.run_with(policies)
        second=self.run_with(policies)
        third=self.run_with(policies)
        self.assertFalse(first["ok"])
        self.assertFalse(second["ok"])
        self.assertFalse(third["ok"])
        self.assertEqual(self.count("claude"),2)
        self.assertTrue(self.breaker.status("claude")["open"])


if __name__ == "__main__":
    unittest.main()
