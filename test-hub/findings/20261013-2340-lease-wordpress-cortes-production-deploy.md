# Lease — WordPress CORTES production deploy

STATUS: RUNNING
AREA: wordpress-cortes-production
DATE: 2026-10-13
OWNER: chatgpt-cortes-finalization
LEASE_START_UTC: 2026-10-13T23:40:00Z
LEASE_EXPIRES_UTC: 2026-10-14T00:10:00Z
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Implantar em produção somente o plugin `anthares-clipper` correspondente ao `main` atual de `UniversoAnthares/anthares-wordpress`, executar lint no servidor e validar a página/estado CORTES sem publicar mídia nem alterar filas sociais.

## Baseline
GitHub WordPress main observado em `2761fda6c894fb4e0aa83baf1a5e4e1b98d85ca5`. O deploy será fail-closed se o HEAD mudar, se o repositório do servidor estiver sujo ou se houver divergência inesperada no plugin ao vivo.

## SUCCESS_SIGNAL
Plugin ativo; arquivos CORTES em produção passam `php -l`; schema CORTES v2 carregado; página `/cortes/` existe e responde; renderização administrativa contém o painel CORTES e a configuração de redes esperada.

## FAILURE_SIGNAL
SSH indisponível; HEAD divergente/sujo; lint falha; WordPress não carrega; página/shortcode ausentes; configuração de redes inesperada.

## TEST_VALIDITY
A validação deve executar no Hostinger real e carregar o `wp-load.php` da instalação `anthares.us`. Probes locais/CI sem acesso ao site não contam como prova de produção.
