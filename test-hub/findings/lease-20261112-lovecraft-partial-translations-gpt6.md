# Lovecraft — reparar traduções parciais sem publicação incompleta
STATUS: RUNNING
AREA: wordpress/lovecraft-publication-recovery
DATE_UTC: 2026-11-12
OWNER: chatgpt-gpt6-lovecraft-partial-20261112
LEASE: ACTIVE_BRANCH_ONLY
BASE_SHA: c5d2364ed5dd75e6a6f383e3e4613289735d3b20
BASELINE_PROVEN: capturas do painel WP do titular: 108 traduzidos, 338 publicados, 6 pendentes, 2 erros; mensagem de quarentena sem lista IDs; scraper executou 2026-11-12 20:00:27. Fonte plugin: anthares_lc_publicar_proxima silencia obras com aviso 'ficaram no idioma original' e retorna texto de quarentena mesmo quando não há nenhuma; tradutor seleciona apenas status 'texto_obtido','pendente'. 
FAILED_AVOIDED: repetir publicar às cegas, limpar avisos sem tradução, marcar incompletos como publicados, criar cron duplicado, estourar cotas dos provedores.
SUCCESS_SIGNAL: PR WordPress com reprocessamento limitado a uma obra parcial/hora, preservação do bloqueio editorial, mensagem distinguindo parcial de quarentena, PHP lint e smoke offline.
FAILURE_SIGNAL: novas publicações de textos com blocos originais, duas obras programadas juntas após retries, consumo de quota sem backoff, mudanças no cron global ou efeitos em outros plugins.
TEST_VALIDITY: alterações de fonte apenas; sem WordPress real, mídia, publicações ou deploy; validar offline e deixar merge para controle coordenado.
SCOPE: anthares-wordpress/anthares-lovecraft-corrigido/includes/{18-executar-traducao.php,19-publicar-post.php}; tests/lovecraft-recovery-contract.php.
