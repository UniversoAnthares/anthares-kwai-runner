# Git provider failover

NORMAL: GitHub is upstream. GitLab and Codeberg receive independent mirrors from GitHub.

GITHUB_UNAVAILABLE: freeze automated mirror writes from GitHub; GitLab becomes the operational source after its HEAD/branch/tag integrity is verified.

GITHUB_AND_GITLAB_UNAVAILABLE: Codeberg becomes the operational source after the same integrity checks.

RECOVERY: fetch refs from every reachable provider; compare branch and tag SHAs. If one valid provider is strictly ahead on the intended lineage, promotion requires an explicit operator action. If providers diverge, automation stops with DIVERGED and performs no merge, reset, force-push, or overwrite.

Protections:
- no provider-to-provider cascade;
- no automatic force-push;
- no automatic reverse synchronization;
- branch and tag refs are checked independently;
- credentials exist only in provider/CI secret stores;
- ambiguous divergence is fail-closed;
- GitHub recovery never overwrites legitimate work automatically.
