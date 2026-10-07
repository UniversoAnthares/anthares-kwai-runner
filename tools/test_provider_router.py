import unittest

from provider_router import (
    CheckpointDiverged,
    DualProviderRouter,
    LeaseConflict,
    ProviderSnapshot,
    ProviderStatus,
    ProviderUnavailable,
)


class Clock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def snap(provider, head, status=ProviderStatus.READY):
    return ProviderSnapshot(provider, "repo", "main", head, status)


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.router = DualProviderRouter(clock=self.clock)
        self.router.update(snap("github", "abc"))
        self.router.update(snap("gitlab", "abc"))

    def test_peer_selection_is_not_fixed_to_one_provider(self):
        first = self.router.acquire("op1", "agent", "repo", "main")
        self.assertEqual(first.provider, "github")
        self.router.complete("op1", "agent")

        second = self.router.acquire("op2", "agent", "repo", "main")
        self.assertEqual(second.provider, "gitlab")

    def test_second_writer_is_blocked(self):
        self.router.acquire("op1", "agent-a", "repo", "main")
        with self.assertRaises(LeaseConflict):
            self.router.acquire("op1", "agent-b", "repo", "main")

    def test_failover_requires_current_provider_to_be_unavailable(self):
        self.router.acquire("op1", "agent", "repo", "main")
        with self.assertRaises(LeaseConflict):
            self.router.failover("op1", "agent")
        self.router.update(snap("github", "abc", ProviderStatus.BLOCKED_QUOTA))
        lease = self.router.failover("op1", "agent")
        self.assertEqual(lease.provider, "gitlab")
        self.assertEqual(lease.generation, 2)

    def test_failover_rejects_divergent_target(self):
        self.router.acquire("op1", "agent", "repo", "main")
        self.router.update(snap("github", "abc", ProviderStatus.DOWN))
        self.router.update(snap("gitlab", "xyz"))
        with self.assertRaises(CheckpointDiverged):
            self.router.failover("op1", "agent")

    def test_no_provider_means_no_execution(self):
        self.router.update(snap("github", "abc", ProviderStatus.BLOCKED_QUOTA))
        self.router.update(snap("gitlab", "abc", ProviderStatus.DOWN))
        with self.assertRaises(ProviderUnavailable):
            self.router.acquire("op1", "agent", "repo", "main")

    def test_expired_lease_can_be_reacquired(self):
        self.router.acquire("op1", "agent-a", "repo", "main", ttl_seconds=10)
        self.clock.advance(11)
        lease = self.router.acquire("op1", "agent-b", "repo", "main")
        self.assertEqual(lease.owner, "agent-b")


if __name__ == "__main__":
    unittest.main()
