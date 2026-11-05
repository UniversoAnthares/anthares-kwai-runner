# AOI13 / seven secondary GitLab backups — lease to sync 3 small source trees
STATUS: RUNNING
AREA: git-redundancy/gitlab-readonly-baseline-and-source-tree-safe-sync
OWNER: chatgpt-20261105
EXPIRES_UTC: 2026-11-05T10:44:11.352Z
CANONICAL_MAIN: 43f00a23ce1025c820f45595cf5d6eacbc0528eb
GOVERNANCE_SHA: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
TARGETS:
- UniversoAnthares/anthares-transcricao GitHub b7d543c2bdd49eb79e14e4adee1a8a6dc9ed45eb -> GitLab 87361771 main 236c6206b61637976f22244f703427fe76ead600, 6 modified/added canonical files.
- UniversoAnthares/home GitHub 1d316d70f0063738a260c45086ff28efb82b662c -> GitLab 87361772 main e325713db3715a217524e226bdccb33dfc68e48b, 5 file updates.
- UniversoAnthares/anthares-telegram-relay GitHub 8eefc5d373ad02e53a5684c78c61291d1f63a9f7 -> GitLab 87361773 main 50f601d0c71b041d48a9114bb735ed1c15d8113b, 5 file updates.
SCOPE: copy exact changed text blobs into non-forced source branches, GitLab MR to main, preserve all other GitLab-only files, history, tags. No CI usage, no media or publisher, no PC executor.
BLOCKING: do not force, do not alter overlapping source histories or binary files. Any per-file/branch ref concurrency or explicit 401/403 stops that repository; no alternate account.
SUCCESS: each GitLab source tree matches GitHub SHA exact changed files with all other blobs unchanged and no forced push. Full git-ref parity remains separately gated (Forgejo HTTP502).
