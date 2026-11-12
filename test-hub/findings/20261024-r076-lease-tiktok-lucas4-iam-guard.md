# Lease — R07.6: TikTok lucasrosalem4 scoped state + IAM contract
STATUS: PARTIAL
AREA: architecture / account-security
DATE: 2026-10-24
RUN: none
JOB: r076-iso05-sec02-iso06-tiktok-lucas4-20261024
COMMIT: base 05ae946b79949cb6d43e4134972c10943c9b62a1
SUPERSEDES: none
LEASE_OWNER: ChatGPT authorized by titular
LEASE_SCOPE: only control_plane/persistent_publisher.py, its unit tests and new account-identity metadata in branch platform/cortes-tiktok-lucas4-account-fence-20261024. No social publication, Neon mutation, secret access, CI production workflow or deploy.
LEASE_START_UTC: 2026-10-24T22:40:20Z
LEASE_EXPIRY_UTC: 2026-10-24T23:10:20Z
LEASE_STATE: ACTIVE

BASELINE_PROVEN: R07.6 audit 218/0; published source blob af8972376fe2cebf50d690c1766e80ebca1f838a; local shadow tests of scoped receipt writer 10/10 PASS, temporary scratch removed. Public identity references: TikTok @lucasrosalem4 and Kwai @lucasrosalem distinct.
FAILED_AVOIDED: old write_receipt had no network verification; merely adding a write_receipt_scoped optional helper left unscoped bypass. New change must make original writer require actor and domain. Preserve existing four tests and other agents' local edits. Security/IAM provider access denied is NOT to be worked around.
SUCCESS_SIGNAL: original API rejects missing scope, kwai-to-tiktok and tiktok-to-kwai, traversal and mismatched receipt; both owned writes succeed; 10+ tests pass; branch and draft PR readback show only intended files; no deploy or production changes.
FAILURE_SIGNAL: any cross-network write succeeds or existing tests fail; branch changed concurrently; secret values logged; any pipeline attempts publication.
TEST_VALIDITY: Python real filesystem in disposable directory, no credentials, OIDC or production. It proves path controls only, NOT real provider IAM or mandatory branch gate. Live credential and deployment acceptance remain independent.

## Checkpoint de encerramento
- LEASE_STATUS: COMPLETE; atualizações feitas somente na branch segregada da PR #1332, sem deploy.
- Run 40140618358 e 40140995938: SUCCESS; testes 10 writer + 11 IAM PASS; verificação negativa de rede cross 6/6 no guard canônico; 23/23 testes da base do clipper PASS.
- Evidência final: test-hub/findings/20261024-r076-tiktok-lucas4-iam-cross-network-qa-partial.md.
- Encerramento: itens 05/07/08 permanecem parciais até provisão/admin IAM e promoção independente; não deixar lease ativo para impedir trabalho de outros agentes.
