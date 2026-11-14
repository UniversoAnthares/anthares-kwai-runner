"""Offline regression; this test does not allocate SpawnDroid devices or log in."""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "tools" / "kwai_spawndroid_session_recovery.py"
spec = importlib.util.spec_from_file_location("kwai_spawndroid_session_recovery", PATH)
m = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = m
spec.loader.exec_module(m)

NOW = datetime(2026, 11, 14, 13, 0, tzinfo=timezone.utc)
PRIMARY = "@universoanthares"
SECONDARY = "@lucasrosalem"
SESSION1 = "session00000000001"
SESSION2 = "session00000000002"
SESSION3 = "session00000000003"


class Tests(unittest.TestCase):
    def setUp(self):
        self.store = m.InMemoryStore()
        self.probes = {}
        self.login_calls = []
        self.login_outcome = m.LoginResult.COMPLETED

        def probe(account, sid):
            return self.probes[(account, sid)]

        def login(account, sid):
            self.login_calls.append((account, sid))
            return self.login_outcome

        self.gate = m.RecoveryCoordinator(
            store=self.store, identity_probe=probe,
            official_login=login, clock=lambda: NOW, production=False)

    def evidence(self, account=PRIMARY, package=None, authenticated=True,
                 uploader=True, challenge=False, checked=None, expires=None,
                 handle=None):
        return m.IdentityObservation(
            account_handle=account if handle is None else handle,
            package=package or m.ACCOUNT_PACKAGES[account],
            authenticated=authenticated, uploader_ready=uploader,
            observed_at=checked or NOW, challenge_required=challenge,
            valid_until=expires)

    def start(self, account=PRIMARY, sid=SESSION1, *, older=False, **kw):
        return self.gate.verify_new_session(
            account, m.ACCOUNT_PACKAGES[account], sid,
            queue_clean=kw.pop("queue_clean", True),
            quota_available=kw.pop("quota_available", True),
            previous_teardown_confirmed=older, **kw)

    def test_two_consecutive_sessions_with_identity_readback(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.probes[(PRIMARY, SESSION2)] = self.evidence()
        self.assertEqual(self.start().status, m.Status.READY)
        self.assertEqual(self.gate.assert_publishable(
            PRIMARY, SESSION1, queue_clean=True).status, m.Status.READY)
        self.assertEqual(self.gate.confirm_teardown(
            PRIMARY, SESSION1, provider_terminal=True).status, m.Status.CLOSED)
        self.assertEqual(self.gate.preflight(
            PRIMARY, queue_clean=True, quota_available=True).status, m.Status.CLOSED)
        self.assertEqual(self.start(sid=SESSION2, older=True).status, m.Status.READY)
        self.assertEqual(self.login_calls, [])
        row = self.store.read(PRIMARY)
        self.assertNotIn(SESSION1, repr(row))
        self.assertNotIn(SESSION2, repr(row))
        self.assertEqual(len(row.session_fingerprint), 64)

    def test_independent_accounts(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.probes[(SECONDARY, SESSION2)] = self.evidence(SECONDARY)
        self.assertEqual(self.start().status, m.Status.READY)
        self.assertEqual(self.start(SECONDARY, SESSION2).status, m.Status.READY)
        self.assertNotEqual(self.store.read(PRIMARY).session_fingerprint,
                            self.store.read(SECONDARY).session_fingerprint)
        self.assertEqual(self.gate.assert_publishable(
            SECONDARY, SESSION1, queue_clean=True).status, m.Status.SESSION_UNVERIFIED)
        self.assertEqual(self.gate.assert_publishable(
            PRIMARY, SESSION2, queue_clean=True).status, m.Status.SESSION_UNVERIFIED)

    def test_previous_session_must_have_terminal_proof(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.probes[(PRIMARY, SESSION2)] = self.evidence()
        self.assertEqual(self.start().status, m.Status.READY)
        self.assertEqual(self.start(sid=SESSION2, older=True).status,
                         m.Status.TEARDOWN_UNVERIFIED)
        self.assertEqual(self.gate.preflight(
            PRIMARY, queue_clean=True, quota_available=True).status,
                         m.Status.TEARDOWN_UNVERIFIED)

    def test_no_previous_terminal_flag_after_close(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.probes[(PRIMARY, SESSION2)] = self.evidence()
        self.start()
        self.gate.confirm_teardown(PRIMARY, SESSION1, provider_terminal=True)
        self.assertEqual(self.start(sid=SESSION2).status, m.Status.TEARDOWN_UNVERIFIED)

    def test_same_session_replay_rejected(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.start()
        self.gate.confirm_teardown(PRIMARY, SESSION1, provider_terminal=True)
        self.assertEqual(self.start(sid=SESSION1, older=True).status, m.Status.SESSION_REUSED)

    def test_mismatched_package_rejected(self):
        with self.assertRaisesRegex(ValueError, "package_account_mismatch"):
            self.gate.verify_new_session(PRIMARY, m.ACCOUNT_PACKAGES[SECONDARY],
                                         SESSION1, queue_clean=True, quota_available=True)
        self.assertIsNone(self.store.read(PRIMARY))

    def test_other_account_identity_rejected(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(handle=SECONDARY)
        self.assertEqual(self.start().status, m.Status.IDENTITY_MISMATCH)
        self.assertFalse(self.gate.assert_publishable(
            PRIMARY, SESSION1, queue_clean=True).can_publish)

    def test_upload_unavailable(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(uploader=False)
        self.assertEqual(self.start().status, m.Status.UPLOAD_UNAVAILABLE)

    def test_mfa_halts_without_login(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(authenticated=False, challenge=True)
        self.assertEqual(self.start(official_login_permitted=True).status, m.Status.NEEDS_HUMAN)
        self.assertEqual(self.login_calls, [])

    def test_official_login_not_permitted_halts(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(authenticated=False)
        self.assertEqual(self.start().status, m.Status.NEEDS_HUMAN)
        self.assertEqual(self.login_calls, [])

    def test_authorized_official_login_requires_second_identity_proof(self):
        calls = [0]
        def probe(account, sid):
            calls[0] += 1
            return self.evidence(authenticated=calls[0] > 1)
        self.gate.identity_probe = probe
        x = self.start(official_login_permitted=True)
        self.assertEqual(x.status, m.Status.READY)
        self.assertEqual(x.strategy, "OFFICIAL_LOGIN")
        self.assertEqual(self.login_calls, [(PRIMARY, SESSION1)])
        self.assertEqual(calls[0], 2)

    def test_login_denial_revocation_and_expiry(self):
        for result, status in (
            (m.LoginResult.DENIED, m.Status.AUTH_DENIED),
            (m.LoginResult.REVOKED, m.Status.AUTH_REVOKED),
            (m.LoginResult.EXPIRED, m.Status.AUTH_EXPIRED),
            (m.LoginResult.HUMAN_CHALLENGE, m.Status.NEEDS_HUMAN),
            (m.LoginResult.UNAVAILABLE, m.Status.PROVIDER_UNAVAILABLE),
        ):
            self.setUp()
            self.probes[(PRIMARY, SESSION1)] = self.evidence(authenticated=False)
            self.login_outcome = result
            self.assertEqual(self.start(official_login_permitted=True).status, status)

    def test_expired_observation(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(
            checked=NOW - timedelta(minutes=3))
        self.assertEqual(self.start().status, m.Status.EVIDENCE_EXPIRED)

    def test_explicit_expiration(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(
            expires=NOW - timedelta(seconds=1))
        self.assertEqual(self.start().status, m.Status.EVIDENCE_EXPIRED)

    def test_ttl_after_five_minutes(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.start()
        self.gate.clock = lambda: NOW + timedelta(minutes=6)
        self.assertEqual(self.gate.assert_publishable(
            PRIMARY, SESSION1, queue_clean=True).status, m.Status.EVIDENCE_EXPIRED)

    def test_publication_uncertain_blocks_following_session(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.probes[(PRIMARY, SESSION2)] = self.evidence()
        self.start()
        self.assertEqual(self.gate.mark_uncertain(PRIMARY, SESSION1).status,
                         m.Status.RECONCILE_REQUIRED)
        self.assertEqual(self.gate.confirm_teardown(
            PRIMARY, SESSION1, provider_terminal=True).status, m.Status.RECONCILE_REQUIRED)
        self.assertEqual(self.gate.preflight(
            PRIMARY, queue_clean=True, quota_available=True).status,
                         m.Status.RECONCILE_REQUIRED)
        self.assertEqual(self.start(sid=SESSION2, older=True).status,
                         m.Status.RECONCILE_REQUIRED)

    def test_unclean_queue_blocks_before_identity_probe(self):
        self.assertEqual(self.start(queue_clean=False).status, m.Status.RECONCILE_REQUIRED)
        self.assertEqual(self.login_calls, [])

    def test_quota_blocks_before_probe(self):
        self.assertEqual(self.start(quota_available=False).status, m.Status.QUOTA_BLOCKED)
        self.assertEqual(self.gate.preflight(PRIMARY, queue_clean=True,
                                             quota_available=False).status,
                         m.Status.TEARDOWN_UNVERIFIED)

    def test_probe_transport_failure(self):
        def fail(*_):
            raise RuntimeError("sensitive raw http response SECRET")
        self.gate.identity_probe = fail
        result = self.start()
        self.assertEqual(result.status, m.Status.PROVIDER_UNAVAILABLE)
        self.assertNotIn("SECRET", repr(result))
        self.assertNotIn("SECRET", repr(self.store.read(PRIMARY)))

    def test_teardown_unverified_retains_block(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.start()
        self.assertEqual(self.gate.confirm_teardown(
            PRIMARY, SESSION1, provider_terminal=False).status,
                         m.Status.TEARDOWN_UNVERIFIED)
        self.assertEqual(self.gate.preflight(
            PRIMARY, queue_clean=True, quota_available=True).status,
                         m.Status.TEARDOWN_UNVERIFIED)

    def test_cas_conflict_fails_closed(self):
        class FailStore(m.InMemoryStore):
            def cas(self, *_):
                return False
        self.gate.store = FailStore()
        self.probes[(PRIMARY, SESSION1)] = self.evidence()
        self.assertEqual(self.start().status, m.Status.CAS_CONFLICT)
        self.assertEqual(self.gate.assert_publishable(
            PRIMARY, SESSION1, queue_clean=True).status, m.Status.SESSION_UNVERIFIED)

    def test_security_denial_survives_teardown(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(authenticated=False)
        self.probes[(PRIMARY, SESSION2)] = self.evidence()
        self.login_outcome = m.LoginResult.DENIED
        self.assertEqual(self.start(official_login_permitted=True).status,
                         m.Status.AUTH_DENIED)
        self.assertEqual(self.gate.confirm_teardown(
            PRIMARY, SESSION1, provider_terminal=True).status, m.Status.AUTH_DENIED)
        self.assertEqual(self.gate.preflight(
            PRIMARY, queue_clean=True, quota_available=True).status, m.Status.AUTH_DENIED)
        self.assertEqual(self.start(sid=SESSION2, older=True).status,
                         m.Status.AUTH_DENIED)

    def test_human_challenge_survives_teardown(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(authenticated=False, challenge=True)
        self.probes[(PRIMARY, SESSION2)] = self.evidence()
        self.assertEqual(self.start().status, m.Status.NEEDS_HUMAN)
        self.assertEqual(self.gate.confirm_teardown(
            PRIMARY, SESSION1, provider_terminal=True).status, m.Status.NEEDS_HUMAN)
        self.assertEqual(self.start(sid=SESSION2, older=True).status, m.Status.NEEDS_HUMAN)

    def test_identity_mismatch_survives_teardown(self):
        self.probes[(PRIMARY, SESSION1)] = self.evidence(handle=SECONDARY)
        self.probes[(PRIMARY, SESSION2)] = self.evidence()
        self.assertEqual(self.start().status, m.Status.IDENTITY_MISMATCH)
        self.assertEqual(self.gate.confirm_teardown(
            PRIMARY, SESSION1, provider_terminal=True).status, m.Status.IDENTITY_MISMATCH)
        self.assertEqual(self.start(sid=SESSION2, older=True).status,
                         m.Status.IDENTITY_MISMATCH)

    def test_in_memory_store_production_refused(self):
        with self.assertRaisesRegex(ValueError, "durable_store_required"):
            m.RecoveryCoordinator(store=m.InMemoryStore(),
                                  identity_probe=lambda *_: self.evidence())

    def test_no_network_or_credentials_in_module(self):
        source = PATH.read_text(encoding="utf-8")
        for forbidden in ("adb backup", "run-as", "cookiejar", "storage_state(",
                          "urllib.request", "requests.post(", "subprocess.run("):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("session00000000001", source)


if __name__ == "__main__":
    unittest.main()
