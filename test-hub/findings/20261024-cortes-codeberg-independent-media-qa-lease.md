# Test Hub — CORTES Codeberg isolated media QA
STATUS: RUNNING
OWNER: ChatGPT
DATE_LOCAL: 2026-10-23
TARGET_CODE: UniversoAnthares/anthares-clipper feature/cortes-cloud-drive-replication-20261023
TARGET_CI: Codeberg UniversoAnthares/anthares-clipper same feature ref
SCOPE: one NEW .forgejo/workflows/cortes-cloud-media-qa.yml, staged push to Codeberg feature branch only; cannot modify main, publish, use API secrets or run GitHub Actions.
BASE_MAIN_CODEBERG: a775b3ee32023732a9107633fba139e32f68b026
BASE_MAIN_GITHUB: a775b3ee32023732a9107633fba139e32f68b026
BASE_FEATURE_GITHUB: 0589d18f9c856922698c77042938baa0e7228ff3
FEATURE_CODEBERG: not present in prior check
CODEBERG_COMPUTE_PROOF: 12 recent Forgejo action runs success, including codeberg-tiny existing admission job; no media FFmpeg proof
POLICY_VERSION: 898630c1c5143f34
SAFETY: push code branch only, with GIT_TERMINAL_PROMPT=0 and credential.interactive=never; do not trigger production main workflows; no new cloud bill, no personal browser interaction.
STOP: on denied Git credentials / branch divergence or external runner limitations; do not bypass authorization or prompt desktop.
