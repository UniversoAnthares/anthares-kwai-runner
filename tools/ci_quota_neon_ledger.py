"""Opt-in PostgreSQL ledger for cancel-first quota attempts across hosts.

The first claimant exclusively owns each attempt. Expiry never permits blind
takeover: recovery needs an independent, externally reconciled procedure.
Importing this module does not connect or dispatch.
"""
from __future__ import annotations

from contextlib import closing
import json
from uuid import uuid4


class StaleQuotaLease(RuntimeError):
    """A worker lost its fencing token or the lease expired."""


class SharedQuotaLedger:
    def __init__(self, connect, *, lease_seconds=120, owner_token=None):
        if not callable(connect):
            raise TypeError("CONNECT_FACTORY_REQUIRED")
        if not isinstance(lease_seconds, int) or not 1 <= lease_seconds <= 3600:
            raise ValueError("INVALID_LEASE_SECONDS")
        self.connect = connect
        self.owner_token = owner_token or str(uuid4())
        self.lease_seconds = lease_seconds
        self._owned = {}

    def claim(self, attempt: str, value: dict) -> tuple[bool, dict]:
        if not attempt or not isinstance(value, dict) or not value.get("state"):
            raise ValueError("INVALID_ATTEMPT")
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
        with closing(self.connect()) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO public.anthares_ci_quota_attempts
                           (attempt_id, owner_token, lease_generation, state, data, lease_until)
                           VALUES (%s, %s::uuid, 1, %s, %s::jsonb,
                                   now() + (%s * interval '1 second'))
                           ON CONFLICT (attempt_id) DO NOTHING
                           RETURNING lease_generation""",
                        (attempt, self.owner_token, value["state"], payload,
                         self.lease_seconds),
                    )
                    created = cur.fetchone()
                    if created is not None:
                        self._owned[attempt] = (int(created[0]), value["state"])
                        return True, dict(value)
                    cur.execute(
                        "SELECT data FROM public.anthares_ci_quota_attempts WHERE attempt_id=%s",
                        (attempt,),
                    )
                    existing = cur.fetchone()
                    if existing is None:
                        raise StaleQuotaLease("CLAIM_RACE_UNCERTAIN")
                    data = existing[0]
                    return False, dict(json.loads(data) if isinstance(data, str) else data)

    def update(self, attempt: str, value: dict) -> None:
        previous = self._owned.get(attempt)
        if previous is None or not value.get("state"):
            raise StaleQuotaLease("NOT_OWNED")
        generation, state = previous
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
        with closing(self.connect()) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE public.anthares_ci_quota_attempts
                           SET state=%s, data=%s::jsonb,
                               lease_generation=lease_generation + 1,
                               lease_until=now() + (%s * interval '1 second'),
                               updated_at=now()
                           WHERE attempt_id=%s AND owner_token=%s::uuid
                             AND lease_generation=%s AND state=%s
                             AND lease_until>now()
                           RETURNING lease_generation""",
                        (value["state"], payload, self.lease_seconds, attempt,
                         self.owner_token, generation, state),
                    )
                    returned = cur.fetchone()
                    if returned is None:
                        self._owned.pop(attempt, None)
                        raise StaleQuotaLease("FENCING_REJECTED")
                    self._owned[attempt] = (int(returned[0]), value["state"])

    def close(self):
        """Connections are opened and closed per transaction."""
        return None
