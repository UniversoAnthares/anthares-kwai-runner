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


def snap(provider, head, status=ProviderStatus.READY, content_id=None):
    return ProviderSnapshot(provider, "repo", "main", head, status, content_id)


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

    def test_failover_allows_different_commits_with_same_content(self):
        self.router.update(snap("github", "gh-commit", content_id="tree-1"))
        self.router.update(snap("gitlab", "gl-commit", content_id="tree-1"))
        self.router.acquire("op-eq", "agent", "repo", "main")
        self.router.update(
            snap("github", "gh-commit", ProviderStatus.BLOCKED_QUOTA, "tree-1")
        )
        lease = self.router.failover("op-eq", "agent")
        self.assertEqual(lease.provider, "gitlab")
        self.assertEqual(lease.generation, 2)

    def test_failover_rejects_different_content_even_with_peer_ready(self):
        self.router.update(snap("github", "gh-commit", content_id="tree-1"))
        self.router.update(snap("gitlab", "gl-commit", content_id="tree-2"))
        self.router.acquire("op-div", "agent", "repo", "main")
        self.router.update(
            snap("github", "gh-commit", ProviderStatus.BLOCKED_QUOTA, "tree-1")
        )
        with self.assertRaises(CheckpointDiverged):
            self.router.failover("op-div", "agent")

    def test_lease_still_fences_same_provider_head_movement(self):
        self.router.update(snap("github", "a", content_id="tree"))
        self.router.acquire("op-fence", "agent", "repo", "main")
        self.router.update(snap("github", "b", content_id="tree"))
        with self.assertRaises(CheckpointDiverged):
            self.router.acquire("op-fence", "agent", "repo", "main")

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
