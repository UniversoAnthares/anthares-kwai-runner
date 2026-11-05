# AOI 7/13 — GitLab primary mirror one-shot restoration
STATUS: RUNNING
OWNER: chatgpt-20261105-gitlab-sync
DATE_UTC: 2026-11-05T10:02:57.411Z
EXPIRES_UTC: 2026-11-05T10:27:57.414Z
MAIN: abc6aa3fba05126ff054fdf3357f12e82106302c
GOVERNANCE_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
SCOPE: sync one primary repo via existing public GitHub-hosted workflow, no Codeberg or Forgejo auth, no PC runner.
PRECHECK: GitHub main latest abc6aa3fba05126ff054fdf3357f12e82106302c; GitLab mirror main d80718910d4e3ea18abc27914e7e67c6b49eead5; prior GitHub run 41260465087 SUCCESS; workflow disabled_manually. GitLab token is existing GH secret. GitLab import includes separate CI commits; retain.
SOURCE_BLOB: d292d48a87574994c8f38e68eec5be540fc5495f; WORKFLOW_BLOB: 898ea2744252e87e8ba5038f9a084eb1ffd5f04d.
FIX: remove forced remote tracking push; remove -X ours auto conflict acceptance; require fast forward or fail closed. No force to any destination. Protect existing GitLab history.
SUCCESS: one existing authenticated workflow dispatch exits 0 with SOURCE_SHA+GITLAB_SYNC PASS; GitLab main includes exact SHA and keeps pre-sync GitLab history; workflow restored disabled_manually.
FAIL: auth 401/403/SSH permission, divergent remote tracking, Git merge conflict, CI quota, uncertain push or concurrent HEAD => stop, inspect and do not retry.
COST: R$0; user PC not executor.
