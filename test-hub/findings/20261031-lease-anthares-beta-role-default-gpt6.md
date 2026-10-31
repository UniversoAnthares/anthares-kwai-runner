# Lease — liberar oferta de conto beta ao papel anthares
STATUS: RUNNING
AREA: wordpress-home-beta-role
DATE: 2026-10-31
RUN: none
JOB: chatgpt-20261031-anthares-beta-role
COMMIT: anthares-wordpress/main ddc5a450ead25d40d4f25af1f5476ca8c63ba8e5
SUPERSEDES: none

## Escopo exclusivo e duração
Owner: ChatGPT/GPT-6, alteração exclusiva em `anthares-pix-sales/includes/65-leitura-beta.php` de `UniversoAnthares/anthares-wordpress`: liberar a usuários com papel exato `anthares` o acesso à funcionalidade "Meus contos para leitura beta" por padrão. Evitar modificar demais permissões, Runas, perfis dos leitores e publicadores. Expiração: 30 minutos após criação deste lease.

## Evidência, sinais e isolamento
BASELINE_PROVEN: a função `anthares_beta_host_pode_disponibilizar_contos` exige Etapa 3; Home, ofertas públicas e configuração usam o mesmo verificador; GitHub e GitLab main contêm o mesmo código-alvo.
FAILED_AVOIDED: alteração apenas cosmética seria insuficiente; desabilitar controles de autoria, nonce ou reserva de Runas seria inseguro.
SUCCESS_SIGNAL: papel `anthares` autorizado na checagem central, usuários comuns continuam exigindo Etapa 3; PHP lint/QA passam e implantação validada à parte.
FAILURE_SIGNAL: regressão em autorização, controles financeiros ou sintaxe.
TEST_VALIDITY: SHA de destino e blob revalidados; alteração isolada; PHP lint e QA sobre conteúdo atualizado.
Sem ação financeira real, nenhuma compra, transferência de Runas ou disponibilização de conto real no teste. Encerrar em finding append-only distinto.