# Correção da configuração de vagas — publicada
STATUS: PROVEN
AREA: wordpress-beta-config-ui
DATE: 2026-10-31
JOB: chatgpt-20261031-beta-config-three-column
COMMIT: 51e2f0a152c577154af419710c1ff43fb66f67bd
SUPERSEDES: test-hub/findings/20261031-lease-beta-config-three-column-gpt6.md

## Alteração
PR WordPress #218 mesclada (commit `51e2f0a152c577154af419710c1ff43fb66f67bd`). Arquivo único `anthares-pix-sales/includes/65-leitura-beta.php`: “Meta de leituras” -> “Quantas vagas?”; descrição -> “Quantos leitores poderão ler simultaneamente?”; checkbox “Disponibilizar este conto” integrado como terceira coluna do grid, ao lado de vagas e Runas. Botão Salvar permanece em linha inferior alinhado à direita; responsividade para larguras menores.

## Provas
- Hostinger, PHP 8.3 lint PASS; manifest 601/601 exactly_once PASS; QA orchestrator PASS.
- Comparação anterior com GitHub main antigo: `LIVE_BASE_MATCH=yes`; backup privado criado antes de publicar.
- Implantação: `DEPLOY_PASS=yes`; SHA-256 do arquivo publicado `8cf53893b8fec9be2b3da013122b47e725bcd5c0bb0675ac9942d6117518087b`.
- WP-CLI: `LABEL=PASS`, `DESCRIPTION=PASS`, `INLINE_TOGGLE=PASS`, `GRID_3_COLUMNS=PASS`, `SAVE_ACTION=PASS`, `ACTIVATION_NAME=PASS`, `RUNTIME_PASS=yes`.
- Conteúdo de produção corresponde ao branch validado: `PRODUCTION_SOURCE_MATCH=PASS`; arquivo publicado PHP lint PASS; `QA_TEMP_CLEANED=yes`.
- Sem oferta salva, alteração de saldo ou teste financeiro; nenhuma escrita de trabalho no PC.
- Primeiro teste de comparação de strings UTF-8 falhou por diferença de codificação no script de validação; repetição com fragmentos ASCII confirmou ambos os rótulos.
- Lease da área encerrado.
