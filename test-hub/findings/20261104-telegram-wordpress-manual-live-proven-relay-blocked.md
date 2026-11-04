# Telegram WordPress — envio manual implantado em producao
STATUS: PROVEN
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: Anthares Remote Cloudflare -> SSH Hostinger PHP 8.5; WordPress WP-CLI read-only
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/221
COMMIT: c8df4230ddee82c29f70399b4f4e5eaf5d2b669b
SUPERSEDES: test-hub/findings/20261104-telegram-wordpress-deploy-lease.md

## Resultado
Implantacao em anthares.us dos arquivos anthares-pix-sales/includes/88-telegram-usuario.php e assets/telegram-usuario.js. Fonte git main fixa c8df4230ddee82c29f70399b4f4e5eaf5d2b669b. Backups privados verificados na Hostinger; nenhum staging no PC. CSS e demais plugins intactos.

## Evidencia
- GitHub PHP blob 5b0ca5395a89cacb536af2ddde79b2e3b253bdcd e JS blob 48ec169cecaf6d87b08c3869225caeba940ddb1b.
- Live Hostinger produziu exatamente os mesmos dois blobs depois de deploy e apos verificador independente; CSS permaneceu 761b27e2f8cdb501b3de06834d293990048de361.
- PHP 8.5 -l PASS antes e depois; JS syntax em V8 PASS.
- QA_MANIFEST_PREFLIGHT=PASS auditable=605 assigned=605 exactly_once=yes.
- JS servido em HTTPS retorna HTTP 200 e git hash-object --stdin = 48ec169cecaf6d87b08c3869225caeba940ddb1b.
- WP-CLI PHP 8.5 com WordPress carregado: RENDER=PASS, PANEL_HIDDEN=PASS, DEEP_LINK=PASS, WEB_FALLBACK=PASS, TOPIC_10898=PASS.
- Backup_count=1, staging_count=0, temp_residues=0; alteracao limitada ao plugin alvo e protected baseline SHA antes de escrever.
- Sem envio de mensagem real ou autenticacao do Telegram; integracao desktop precisa teste humano de rascunho.

## Pendente independente
Relay Python MTProto do Railway segue bloqueado: os 2 projetos do workspace estao FAILED no build e acompanham main. PR #5 corrige Docker VOLUME e idempotencia; PR #6 corrige acesso ao volume, necessaria reconciliacao. Railway publica plano Free por $0 com credito $1/mes, mas a conta conectada nao expos comprovacao do plano atual nem limite de uso/cobranca; sem autorizacao para novo custo R$0, nenhum deploy Railway foi executado. Hostinger Web/Cloud nao hospeda apps Python persistentes segundo suporte oficial, sem VPS adicional. Vinculacao/envio automatico ainda OFFLINE.
Lease encerrado. Status PROVEN apenas para implantacao WordPress do envio manual.
