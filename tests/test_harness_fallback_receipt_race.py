"""Regression: GitHub workflow can start before watcher stores dispatch ACK."""
import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from tools import harness_fallback_receipt as receipt

SHA = "a" * 40
EXEC = "abcdefghijklmnop"


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class FallbackReceiptRaceTests(unittest.TestCase):
    def test_start_waits_for_ack_without_duplicate_dispatch(self):
        calls = []
        def opener(req, timeout=None):
            calls.append(req.full_url)
            if len(calls) == 1:
                return Response(json.dumps({"value": "oidc"}).encode())
            if len(calls) in (2, 3):
                raise HTTPError(req.full_url, 409, "waiting", {}, Response(
                    json.dumps({"code": "NOT_RESERVED_OR_ALREADY_EXECUTING"}).encode()))
            return Response(json.dumps({"code": "FALLBACK_EXECUTION_AUTHORIZED"}).encode())
        with patch.dict(os.environ, {
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.invalid/oidc",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "request"}, clear=True), \
             patch.object(receipt.urllib.request, "urlopen", opener), \
             patch.object(receipt.time, "sleep") as sleep:
            receipt.submit("start", SHA, EXEC)
        self.assertEqual(len(calls), 4)
        sleep.assert_any_call(2)
        self.assertEqual(sleep.call_count, 2)

    def test_other_conflict_does_not_retry(self):
        calls = []
        def opener(req, timeout=None):
            calls.append(req.full_url)
            if len(calls) == 1:
                return Response(json.dumps({"value": "oidc"}).encode())
            raise HTTPError(req.full_url, 409, "not authorized", {}, Response(
                json.dumps({"code": "FENCING_REJECTED"}).encode()))
        with patch.dict(os.environ, {
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.invalid/oidc",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "request"}, clear=True), \
             patch.object(receipt.urllib.request, "urlopen", opener), \
             patch.object(receipt.time, "sleep") as sleep:
            with self.assertRaises(HTTPError):
                receipt.submit("start", SHA, EXEC)
        self.assertEqual(len(calls), 2)
        sleep.assert_not_called()

    def test_finish_never_retries_uncertain_conflict(self):
        calls = []
        def opener(req, timeout=None):
            calls.append(req.full_url)
            if len(calls) == 1:
                return Response(json.dumps({"value": "oidc"}).encode())
            raise HTTPError(req.full_url, 409, "conflict", {}, Response(
                json.dumps({"code": "NOT_RESERVED_OR_ALREADY_EXECUTING"}).encode()))
        with patch.dict(os.environ, {
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.invalid/oidc",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "request"}, clear=True), \
             patch.object(receipt.urllib.request, "urlopen", opener), \
             patch.object(receipt.time, "sleep") as sleep:
            with self.assertRaises(HTTPError):
                receipt.submit("finish", SHA, EXEC)
        self.assertEqual(len(calls), 2)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
