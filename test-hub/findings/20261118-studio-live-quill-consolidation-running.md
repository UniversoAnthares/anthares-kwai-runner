# Studio — consolidação Quill do runtime e PR #333

STATUS: RUNNING
DATE: 2026-11-18
AREA: anthares-studio/release/staging-live-quill-safety
OWNER: ChatGPT / OBSERVATORIO IPB
JOB: studio-live-quill-consolidation-20261118
SOURCE: UniversoAnthares/anthares-wordpress PR #333 HEAD 31620cf60e5642845160137f8c88fb6a8ba20948
TARGET_BRANCH: integration/studio-live-quill-safety-20261118
PEER: GitLab branch integration/studio-live-quill-safety-20261118 absent (404).
GOVERNANCE: REGRAS-OBRIGATORIAS.md/INDICE.md lidos na máquina autorizada (2026-11-18); Test Hub README lido.

## Baseline
- WordPress plugin original SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.
- Studio live JS SHA256 1b2b499310e28db0abb9bd0c3085c2ac4d0fd381208378b8e8602224f1, blob Git fc71a0ea4cf0578820b753fafc3ab625420f688d.
- Live Studio WP options anst_writes_enabled=1, anst_acf_runtime_enabled=1; 19 ACF groups, 20/20 live unittest PASS, PHP 8.3 lint PASS, 71 AEST vs 73 ANST.
- O live JS possui Quill2 guard e protege falha de importação, porém sem history.clear depois de setContents; o select narrativo ainda integra o toolbar; branch #333 contém ambos patches. A diferença live/branch é pequena e inclui texto da lixeira, tabs 9 x 7 e toolbar.
- PR Test Hub #2654 possui lease RUNNING para patch Quill2 em produção. Não tocar arquivo ativo nem branch PR #330, #332, #333.

## Escopo e limites
Preparar **branch independente** reconciliando versão ativa da Hostinger com patches de segurança do Quill (#332/#333), preservando os ajustes mais recentes de produção para lixeira e demais funções. Nenhum deploy sem reconciliar owner/lease, backup/rollback, testes reais e autorização da ferramenta. O teste de escrita REST autenticada foi explicitamente bloqueado anteriormente e não será refeito por outro canal.

## QA planejado
Clone efêmero privado Hostinger, diff read-only + overlay estritamente em JS, regressões e Node syntax, PHP lint, testes Python, manifesto QA exactly-once, remoção do clone. Estabelecer HEAD de recuperação da instalação e homologação sem mutação dos dados.
SUCCESS_SIGNAL: branch registrada, hash de produção conferido, QA limpa do checkout final, prova append-only.
FAILURE_SIGNAL: alterações concorrentes, testes falhos, divergência de hash, tentativa de tocar produção.
ROLLBACK: descartar esta PR draft, sem efeito em produção.
