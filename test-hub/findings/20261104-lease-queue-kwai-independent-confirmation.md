# Lease — Kwai: proibir confirmação autodeclarada no contrato Neon
STATUS: RUNNING
AREA: queue
DATE: 2026-11-04
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2057
JOB: none
COMMIT: 6217c31c713e1e204c8f80c2cf1bc83f53bc284b
SUPERSEDES: none
LEASE_OWNER: ChatGPT / Reestruturação e Otimização / CORTES
LEASE_START_UTC: 2026-11-04T02:45:54.965Z
LEASE_EXPIRES_UTC: 2026-11-04T03:15:54.965Z
GOVERNANCE_MANIFEST: 223433740e807a90
TARGET_BRANCH: optimization/20261103-kwai-neon-ha-failclosed
TARGET_HEAD_SHA: 6edb1e00c54a378da79e670746becd4fb389bf2f

## BASELINE_PROVEN
- 68 uncertain no alvo kwai:lucasrosalem sem remote_id ou confirmação, preservar 68.
- 68/68 mídias externas WordPress HTTP HEAD 200 e Neon ledger rev 15399 com hash íntegro (finding 20261104-cortes-media-68-head-ledger-recovery-verified.md).
- PR #2057 draft, sem deploy; confirmações baseadas só em `proof.kind/method/url/account` enviados pelo publicador podem ser autodeclaradas, mesmo com URL formatada corretamente.
- O role `probe` foi criado para outros testes e não deve ler registros Kwai privados fora de escopo.
- SHA main 6217c31c713e1e204c8f80c2cf1bc83f53bc284b, branch 6edb1e00c54a378da79e670746becd4fb389bf2f; espelho GitLab pode divergir.

## SUCCESS_SIGNAL
- PR #2057 exige assinatura HMAC verificável e fresca, vinculada a conta, job, lease_generation, mídia, ID do vídeo, URL e método, originada de verificador independente; chave de assinatura não configurada => confirmação bloqueada.
- `kwai-uncertain-read` limitado a um workflow Kwai próprio, default-off e sem exposição para `probe` de outros alvos.
- Testes isolados demonstram rejeição de proof autodeclarado, assinatura inválida, expirada e geração incorreta, sem conexão à rede ou escrita em banco.

## FAILED_AVOIDED
- Não inserir segredos nem chave HMAC em Git, logs, testes ou arquivo de finding.
- Não criar novo serviço ou quota, ativar publicadores, misturar identidades, publicar para testar ou alterar 68 registros.
- Não mesclar PR draft nem instalar função Neon/Worker em produção sem QA, quota e autorização de titular.

## TEST_VALIDITY
Escopo restrito ao contrato de QA em branch já existente e testes sintéticos. Encerrar lease por finding após verificação. Nova lease para implantação/ativação real.
