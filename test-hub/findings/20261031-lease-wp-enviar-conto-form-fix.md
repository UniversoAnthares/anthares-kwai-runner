# Lease — formulário Enviar conto
STATUS: RUNNING
AREA: wordpress-enviar-conto
DATE: 2026-10-31
RUN: Hostinger SSH
JOB: chatgpt-20261031-enviar-conto
COMMIT: c29c355f7f9e99353369f0539e6cc6ad25b8bad1
SUPERSEDES: none

BASELINE_PROVEN: browser mostra Palavras: 0 com conteúdo, botão Enviar bloqueado e Salvar beta inoperante. Tema carrega `wordCounter.js`, onde detecção do TinyMCE na inicialização é insuficiente, e guarda de submissão verifica exclusivamente o botão Enviar. Fluxo beta implementado em plugin `65-leitura-beta.php`.
FAILED_AVOIDED: evitar criar/publicar contos reais, transações ou mexer em runner Windows. Testes externos: php -l PASS, manifest 599/599 PASS, orchestrator PASS.
SUCCESS_SIGNAL: contador acompanha editor, botão Enviar respeita 1000-2000 palavras + opções, Salvar beta segue independente e registra o formulário. Produção corresponde ao commit e WP-CLI carrega plugin.
FAILURE_SIGNAL: falha PHP/JS, base divergente, submissão beta impede publicação normal, erro de autorização ou controle financeiro.
TEST_VALIDITY: HEAD e SHA dos arquivos confirmados; testes externos, inspeção HTTP, sem criar conteúdo real.
OWNER: ChatGPT/GPT-6. Lease expirável após 30 minutos; exclusivamente `anthares-pix-sales/includes/65-leitura-beta.php`.
