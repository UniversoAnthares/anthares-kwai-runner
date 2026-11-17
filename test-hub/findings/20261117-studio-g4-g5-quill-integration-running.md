# Studio G4+G5 — integração segura de correções com testes QA

STATUS: RUNNING
AREA: anthares-studio/integration/g4-g5-quill
DATE: 2026-11-17
OWNER: ChatGPT / OBSERVATORIO IPB
JOB: studio-g4-g5-quill-integration-20261117
SOURCE: PR #316 HEAD cc9f0d07cb7e4d2338d4da9b640c901b88ffe74c; PR #317 HEAD 4d2b12a2d8a81a57b3448a952f464985f8204c11; PR #319 HEAD 599a72284e61510ec2f7e92e518f490e02a5a541
PEER: GitLab branch integration/studio-g4-g5-quill-qa-20261117 absent 404.
BASELINE_PROVEN: PR316 66/66 Python, PR317 58/58, PR319 67/67 on separate isolated checkout, no live REST writes. Production ACF OFF, 71 migrated, original plugin SHA unchanged.
FAILED_AVOIDED: nenhum merge em branch compartilhada PR316, nenhum deploy, nada do legado. PR318 G7 possui escopo independente e não será sobrescrita.
SCOPE: branch NOVA somente. Transplantar (i) correção Quill e teste da PR319, (ii) CPT show_ui com capabilities admin e teste da PR317, (iii) passo QA manual da PR317. Aplicar alterações mínimas ao PHP atual da PR316 para preservar correções recentes do G4. Validar HEAD integrada em clone efêmero Hostinger.
SUCCESS_SIGNAL: >=68 testes Python PASS, PHP lint, manifesto 665/665 e orquestrador PASS, Node syntax; nenhum conflito de arquivos.
FAILURE_SIGNAL: teste quebrado, mismatch de SHA, alteração em arquivo legado, merge/deploy sem autorização G4.
TEST_VALIDITY: valida código e contratos integrados; não prova frontend autenticado ou escrita REST real.
ROLLBACK: descartar PR draft; remover clone temporário.
