# Configuração das ofertas beta — formulário corrigido em produção
STATUS: PROVEN
AREA: wordpress-beta-config-ui
DATE: 2026-10-31
RUN: Hostinger SSH / WP-CLI
JOB: chatgpt-20261031-beta-config-ui
COMMIT: d63486f9d96a3685c4e4def87b718925f10be34c
SUPERSEDES: test-hub/findings/20261031-lease-beta-config-ui-gpt6.md

## Mudança
- PR WordPress #216 mesclada em `main`; apenas `anthares-pix-sales/includes/65-leitura-beta.php` alterado.
- Página `/leitura-beta/?configurar=contos`: título isolado, linha de indicadores espaçada, status de oferta, campos numéricos em duas colunas e responsivos.
- Checkbox nativo com rótulo visível **Disponibilizar este conto** e explicação da publicação e da reserva de Runas. Alinhamento e botão de salvamento reorganizados.
- Nomes dos campos, nonce, backend de ofertas e reserva financeira preservados.

## Evidência
- GitHub PR #216 merge `d63486f9d96a3685c4e4def87b718925f10be34c`.
- Arquivo da produção era idêntico ao GitHub main antes da alteração. Implantação atômica com backup privado em Hostinger, `BETA_CONFIG_DEPLOY_PASS`.
- PHP 8.3 lint PASS. Manifest 601/601 PASS; orquestrador QA PASS.
- WP-CLI leu HTML gerado para conta com papel `anthares`: TITLE PASS, STATUS_ROW PASS, CHECKBOX_LABEL PASS, FIELDS PASS, CSS_RULES PASS, RUNAS_READONLY PASS.
- Primeira comparação textual da ajuda sinalizou FAIL em verificadora de string exata; inspeção dedicada do HTML renderizado confirmou mensagem integral: 'Ao ativar, o conto aparecerá nas ofertas de leitura beta e as Runas necessárias serão reservadas.' A causa era a comparação textual do teste, sem ausência da mensagem.
- `CODE_PRODUCTION_MATCH=yes` byte a byte após implantação, PHP lint de produção PASS, `TEMP_CLEANED=yes`.
- Nenhuma oferta salva, ativada ou paga em QA. Nenhum artefato novo no computador do usuário. Leases encerrados.
