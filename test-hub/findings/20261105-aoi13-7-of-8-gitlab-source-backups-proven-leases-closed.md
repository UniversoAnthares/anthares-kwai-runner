# AOI 7/13 — GitLab source recovery, 2026-11-05
STATUS: PARTIAL — seven of eight GitLab repository source backups current; Forgejo origin down.
AREA: git-redundancy/gitlab-source-tree-recovery
LEASE: CLOSED
SUPERSEDES:
- lease-20261105-aoi13-gitlab-safe-mirror.md
- lease-20261105-aoi13-three-gitlab-tree-sync.md
- lease-20261105-aoi13-wordpress-gitlab-full-mirror.md
OWNER: chatgpt-aoi13-20261105
GOVERNANCE_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
GITLAB_REF_PUSH_FORCE: false
PERSONAL_PC_EXECUTION: false
PAID_RESOURCES: false
SOCIAL_PUBLICATIONS: zero

## Results
1. `anthares-kwai-runner`: PR #2117 merged GitHub commit `43f00a23ce1025c820f45595cf5d6eacbc0528eb`. One existing hosted workflow run 42007685862 job 127178494834 SUCCESS: `SOURCE_SHA=43f00a23...`, `GITLAB_MAIN_SHA=ecc232859e19f9d8fe03fcb6aa483a8e91c85c1a`, `PRESERVED_GITLAB_HISTORY=PASS`, `GITLAB_SYNC=PASS`. The script now refuses divergent source tracking and textual conflicts; no force remote push or -X ours. Workflow restored disabled_manually.
2. `home`: GitLab MR !1 merged `46aca2ae99447b74dc8c931576327a39b457c8e7`, exact source tree 5/5 blobs.
3. `anthares-transcricao`: GitLab MR !4 merged `074449ac6a56957c9f3b1bc392b57e25dceaeabe`, exact source tree 15/15 blobs, including missing workflow.
4. `anthares-telegram-relay`: GitLab MR !4 merged `42f78dddeca519d92f9e08184915c230a28a98c8`, exact source tree 17/17 blobs.
5. `anthares-wordpress`: existing approved fenced mirror run 42009258489 job 127183785067 SUCCESS, source SHA e89aee9f53b42199bc9cf9691fa5b259b79edb0d; GitLab main updated `9ea3e3b641229cb69988c3c8233dd69284429335`; logged `MERGED_PRESERVING_BOTH`. Independent full tree after run 740/740 exact blobs, zero extra/changed files. Fallback workflow restored disabled_manually.
6. `wiki`: existing GitLab source commit found, tree 6/6 identical; no write needed.
7. `github-slideshow`: existing GitLab source commit found, all 140 source blobs identical; five GitLab-specific additional files retained. No write needed.

## Outstanding
- `anthares-clipper`: private repo main 52987aed165f3682ef6c5f5ec0774b76bad94893, GitLab 87361774 main 1eab2129e71027a14e68407f52e86e643c0ada2b. Source 544 blobs, GitLab 239 blobs, 339 missing/different and 7 GitLab-only files. Existing GitHub repository has no configured GitLab write secret according to authorized name-only secret check. Safely reconciling complete Git ancestry still requires legitimate hosted credentials and protected Git history; do not turn 339 files into a lossy overwrite or use the user PC as runner. No 403 bypass.
- Hostinger Forgejo main origin last observed HTTP502, /forgejo-sync.php HTTP503. Full 15-repo current ref parity cannot be confirmed or repaired via authorized admin route; no bypass of earlier security refusal.
- The final task-state is AOI #7 PARTIAL and #13 BLOCKED/PARTIAL work performed. Independent GitLab backup of 7/8 repositories is current; continuity scheduling remains disabled under cost reduction. Historic Forgejo code-provisioned item #20 remains separate.

## Acceptance
All successful GitLab merges preserve GitLab previous history and did not force refs. Source tree of home/transcricao/telegram and WordPress verified by one post-change independent compare, with no subsequent duplicate QA. No runner jobs except one core GitLab sync and one WordPress fenced mirror. No social or Android publish activity.
