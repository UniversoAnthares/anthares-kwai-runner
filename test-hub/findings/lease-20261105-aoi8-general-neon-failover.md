# AOI #8 — general quota controller on free Neon
STATUS: RUNNING
AREA: ci-quota-failover/oidc-neon-general
OWNER: chatgpt-aoi8-20261105
EXPIRES_UTC: 2026-11-05T04:14:54.932Z
BASE_HEAD: ccf61aa3326ebea8d32e2c69fefb38aec269ab3a
GOVERNANCE_SHA: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
ITEMS: [8]
CURRENT: Vercel reserve/ack/confirm all HTTP402, Neon cquotarec historical confirm HTTP200, 19/19 confirmed. Existing workflow disabled_manually.
PEER: GitLab project 87307248 main watcher e2dda629d37cc3bbb8f7a36c0810801a5a8b7485 differs from current GitHub 1a3f6188d1094326442ecca2a975d33564da1881; no GitLab write.
SCOPE: widen existing free Neon function to authenticated reserve/ack/confirm preserving old readback, update canonical watcher URL to Neon; no dispatch of new quota rescue or social publication.
SUCCESS: function deploy HTTP200 and unauth POST HTTP401, GitHub source matches deployed archive, old 19 receipts stay confirmed; optional one read-only watcher when quota allows. Leave main workflow disabled manually.
FAIL: any unauthorized write, CAS skip, CI workflow accidentally active, paid resource, remote GitLab permission denial; fail closed.
