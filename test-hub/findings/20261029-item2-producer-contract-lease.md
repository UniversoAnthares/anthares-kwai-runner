# Item 2 — lease para corrigir contrato de testes do produtor TikTok
STATUS: RUNNING
AREA: tiktok/forgejo-producer-contract
DATE: 2026-10-29 UTC
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40880594122
JOB: 123470743304
COMMIT: ac092439054a00942f95ed957bfab22fc1318e22
SUPERSEDES: none
LEASE: arquivo exclusivo UniversoAnthares/anthares-clipper/tests/test_cortes_tiktok_enqueue.py; titular da execução ChatGPT item2; liberar após PR/CI e readback. Não modificar o código produtivo do producer/Forgejo, nem Neon, credenciais, runners, flags ou mídias.

EVIDENCE: GitHub CORTES TikTok producer contract, job 123470743304, test suite 10 cases, 4 failures and 1 error. Production producer calls from cortes_tiktok_enqueue.eligible() the canonical attachment editorial_for_clip(c) in cortes_editorial_transport.py. Existing fixtures assert legacy inline clip.titulo, have no canonical attachment metadata and no mock for the attachment lookup. Missing WP context means editorial_for_clip rejects, and eligible returns zero rows. Tests are stale relative to enforced canonical-media policy, not evidence that real WordPress attachments are corrupt.
CHANGE: Update ONLY test fixtures to emulate canonical verified WordPress attachment metadata and assert failures quarantine invalid attachment metadata. Keep production fail-closed and no use of clip.titulo for final metadata. No network tests; one controlled contract CI run on PR.
EVIDENCE_OF_SUCCESS: suite 10/10+ passes, CI run SUCCESS, source SHA fixed; original run #40880594122 remains FAILED historically, and no social publication or Forgejo productive handoff is claimed.
SECURITY: do not create local files on user Windows, read credentials, modify existing publishing or retry uncertain jobs.