"""No-network simulated tests for the cross-host Postgres CAS contract."""
import unittest
from tools.ci_quota_neon_ledger import SharedQuotaLedger, StaleQuotaLease


class Database:
    def __init__(self):
        self.rows = {}
        self.expired = False
        self.queries = []

    def connect(self):
        return Connection(self)


class Connection:
    def __init__(self, db):
        self.db = db
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def cursor(self):
        return Cursor(self.db)
    def close(self):
        pass


class Cursor:
    def __init__(self, db):
        self.db = db
        self.result = None
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, sql, params):
        self.db.queries.append(sql)
        op = sql.strip().split()[0]
        if op == "INSERT":
            attempt, owner, state, data, seconds = params
            self.result = None
            if attempt not in self.db.rows:
                self.db.rows[attempt] = {"owner": owner, "generation": 1,
                    "state": state, "data": data, "seconds": seconds}
                self.result = (1,)
        elif op == "SELECT":
            row = self.db.rows.get(params[0])
            self.result = (row["data"],) if row else None
        elif op == "UPDATE":
            state, data, seconds, attempt, owner, generation, previous = params
            row = self.db.rows.get(attempt)
            self.result = None
            if (row and not self.db.expired and row["owner"] == owner
                and row["generation"] == generation and row["state"] == previous):
                row.update(generation=generation+1, state=state, data=data)
                self.result = (generation+1,)
        else:
            raise AssertionError("unexpected SQL")
    def fetchone(self):
        return self.result


class SharedLedgerTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.first = SharedQuotaLedger(self.db.connect, owner_token="11111111-1111-4111-8111-111111111111")
        self.other = SharedQuotaLedger(self.db.connect, owner_token="22222222-2222-4222-8222-222222222222")
        self.seed = {"state":"CANCEL_REQUESTED","task":"task-1"}

    def test_first_claim_is_exclusive(self):
        self.assertTrue(self.first.claim("a-1",self.seed)[0])
        won, saved = self.other.claim("a-1",{"state":"CANCEL_REQUESTED"})
        self.assertFalse(won)
        self.assertEqual(saved,self.seed)

    def test_fenced_update_increments_generation(self):
        self.first.claim("a-1",self.seed)
        self.first.update("a-1",{"state":"CANCEL_UNCONFIRMED"})
        self.assertEqual(self.db.rows["a-1"]["generation"],2)
        self.assertEqual(self.db.rows["a-1"]["state"],"CANCEL_UNCONFIRMED")
        self.assertTrue(any("lease_generation=lease_generation + 1" in s for s in self.db.queries))

    def test_second_host_cannot_update(self):
        self.first.claim("a-1",self.seed)
        self.other.claim("a-1",self.seed)
        with self.assertRaisesRegex(StaleQuotaLease,"NOT_OWNED"):
            self.other.update("a-1",{"state":"FALLBACK_QUEUED"})

    def test_expired_lease_rejects_update_and_never_auto_reclaims(self):
        self.first.claim("a-1",self.seed)
        self.db.expired=True
        with self.assertRaisesRegex(StaleQuotaLease,"FENCING_REJECTED"):
            self.first.update("a-1",{"state":"CANCELLED_QUOTA"})
        self.assertFalse(self.other.claim("a-1",self.seed)[0])

    def test_changed_generation_fails_closed(self):
        self.first.claim("a-1",self.seed)
        self.db.rows["a-1"]["generation"]=23
        with self.assertRaises(StaleQuotaLease):
            self.first.update("a-1",{"state":"FALLBACK_RESERVED"})

    def test_invalid_attempt_or_lease(self):
        with self.assertRaises(ValueError):
            self.first.claim("",self.seed)
        with self.assertRaises(ValueError):
            SharedQuotaLedger(self.db.connect,lease_seconds=0)


if __name__ == "__main__":
    unittest.main()
