# AOI #16 — one-line fanout P0 repair lease
STATUS: RUNNING
OWNER: chatgpt-aoi16-20261105
AREA: qa-p0-cortes-buffer-fanout-runner-identity
DATE_UTC: 2026-11-05T03:21:05.416Z
EXPIRES_UTC: 2026-11-05T03:51:05.418Z
BASE_HEAD: fa5385376edbeacea7e07909ea0fd3e7d1ecc26b
GOV_SHA: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
ITEMS: [16]
SOURCE_BLOB: a6c589240f6d9c485618f1f57f50fe660748717e
PEER_GITLAB_BLOB: a6c589240f6d9c485618f1f57f50fe660748717e
SOURCE_RUN: 41265680140, job 124727889316 failed immediately CORTES_BUFFER_FANOUT_FAILED=RuntimeError without destination logs.
CAUSE: tools/cortes_buffer_three_fanout.py calls linked.require_cloud() before any network. That gate demands RUNNER_ENVIRONMENT=github-hosted but workflow omits this variable. GitHub sets RUNNER_OS=Linux and GITHUB_ACTIONS=true.
SCOPE: add only RUNNER_ENVIRONMENT: github-hosted to the workflow; no other code, no publication, no migration, no credential changes.
SAFETY: workflow was disabled_manually; leave disabled; do not dispatch to avoid paid quotas or publishing. Minimal static readback only; true publication incident remains open for independent proof.
SUCCESS_SIGNAL: current canonical workflow has exact required identity field, disabled state preserved; one-line source merged and read back.
