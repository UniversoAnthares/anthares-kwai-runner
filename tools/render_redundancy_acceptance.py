#!/usr/bin/env python3
"""Acceptance tests for Anthares runtime redundancy.

Render is treated as one execution provider. Cloudflare anthares-control remains
single authority for durable state/fencing, while provider policy can move an
operation to GitHub/GitLab when Render is unavailable.
"""

from provider_router import (
    CheckpointDiverged,
    DualProviderRouter,
    ProviderSnapshot,
    ProviderStatus,
)

REPO = "UniversoAnthares/anthares-kwai-runner"
REF = "main"
HEAD = "abc123"
TREE = "tree123"


class Clock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value

    def tick(self, seconds=1):
        self.value += seconds


def snap(provider, status=ProviderStatus.READY, head=HEAD, content_id=TREE):
    return ProviderSnapshot(provider, REPO, REF, head, status, content_id)


def test_render_failure_moves_lease_to_peer():
    clock = Clock()
    router = DualProviderRouter(("render", "github", "gitlab"), clock=clock)
    for provider in ("render", "github", "gitlab"):
        router.update(snap(provider))

    lease = router.acquire("op-1", "worker-1", REPO, REF, ttl_seconds=120)
    assert lease.provider == "render"
    assert lease.generation == 1

    router.update(snap("render", ProviderStatus.DOWN))
    moved = router.failover("op-1", "worker-1", ttl_seconds=120)
    assert moved.provider == "github"
    assert moved.generation == 2

    # Render recovery must not steal the active lease back.
    router.update(snap("render", ProviderStatus.READY))
    renewed = router.renew("op-1", "worker-1", ttl_seconds=120)
    assert renewed.provider == "github"
    assert renewed.generation == 2

    final = router.complete("op-1", "worker-1")
    assert final.content_id == TREE


def test_second_failover_reaches_gitlab():
    clock = Clock()
    router = DualProviderRouter(("render", "github", "gitlab"), clock=clock)
    for provider in ("render", "github", "gitlab"):
        router.update(snap(provider))

    lease = router.acquire("op-2", "worker-2", REPO, REF)
    assert lease.provider == "render"
    router.update(snap("render", ProviderStatus.DOWN))
    lease = router.failover("op-2", "worker-2", target_provider="github")
    assert lease.provider == "github" and lease.generation == 2
    router.update(snap("github", ProviderStatus.DOWN))
    lease = router.failover("op-2", "worker-2", target_provider="gitlab")
    assert lease.provider == "gitlab" and lease.generation == 3


def test_divergent_backup_is_fail_closed():
    clock = Clock()
    router = DualProviderRouter(("render", "github"), clock=clock)
    router.update(snap("render"))
    router.update(snap("github"))
    router.acquire("op-3", "worker-3", REPO, REF)
    router.update(snap("render", ProviderStatus.DOWN))
    router.update(snap("github", ProviderStatus.READY, head="different", content_id="different-tree"))
    try:
        router.failover("op-3", "worker-3")
    except CheckpointDiverged:
        return
    raise AssertionError("divergent provider was incorrectly accepted")


def test_expired_lease_can_be_reacquired():
    clock = Clock()
    router = DualProviderRouter(("render", "github"), clock=clock)
    router.update(snap("render"))
    router.update(snap("github"))
    first = router.acquire("op-4", "worker-a", REPO, REF, ttl_seconds=10)
    assert first.provider == "render"
    clock.tick(11)
    second = router.acquire("op-4", "worker-b", REPO, REF, ttl_seconds=10)
    assert second.owner == "worker-b"
    assert second.provider == "github"


def main():
    tests = [
        test_render_failure_moves_lease_to_peer,
        test_second_failover_reaches_gitlab,
        test_divergent_backup_is_fail_closed,
        test_expired_lease_can_be_reacquired,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"RENDER_REDUNDANCY_ACCEPTANCE_OK={len(tests)}")


if __name__ == "__main__":
    main()
