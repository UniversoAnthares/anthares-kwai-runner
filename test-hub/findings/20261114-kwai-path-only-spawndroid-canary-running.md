# Kwai regular no SpawnDroid — canário path-only com alterações causais
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: nenhum workflow GitHub, teste Appium isolado via ARA + CDP autenticado
JOB: sessão CI única, acompanhamento no mesmo turno
COMMIT: base 9970cb85e6f094a78a4c9e39edca5cec676423e7
SUPERSEDES: none
OWNER: ChatGPT item1, teste único, sem agentes concorrentes
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## BASELINE_PROVEN
- Teste anterior sess_4139ebebc97647c894: SpawnDroid CI session boot, webdriver ativo, instalador 25 URLs com '?e=&s=' retornou HTTP500. Sessão terminada, sem login/publicação.
- Hostinger SSH direto: 25/25 APKs originais com SHA256 correto, tamanho total 202108730 bytes; auditoria independente da assinatura digital APK v2 e do content digest dos 25 arquivos foi concluída com exit0.
- Nova regra Hostinger .htaccess publicada em 14/11: /signed/<expiry>/<sig>/<filename>.apk reescreve para fetch.php?f=...&e=...&s=... . URL agora termina em .apk e não contém query; mesma HMAC. Testes: GET200 tamanho12754 hash válido, HEAD200, assinatura inválida 403, HEAD URL antiga 200. Backup privado htaccess-backup-item1-20261114.
- API CI SpawnDroid exige artefato pré-cadastrado; demo original serve somente de portador do canário. Cloud cutover false.

## FAILED_AVOIDED
Não repetir URLs query antigas; não usar testes com login ou postagem; não compartilhar segredo HMAC, signed URLs, logs de sessão ou cookies; não alterar demo, contas, publicadores ou produção.

## SUCCESS_SIGNAL
Uma sessão CI nova (idempotência única), profile android-14-phone, demo artifact existente, webdriver pronto, mobile: installMultipleApks usando 25 URL assinadas terminadas em .apk, package com.kwai.video instalado e app visível via fonte UI, sessão WebDriver e sessão CI explicitamente encerradas, GET /api/sessions confirma endedAt. Nenhum login/vídeo.

## FAILURE_SIGNAL
Cota 402, slot 429, sessão boot falha, 500 Appium, APK 403/404, app não instala ou fecha; capturar somente código e erro sanitizado, encerrar ambas as sessões. Não repetir até nova hipótese.
 
## TEST_VALIDITY
Canário de instalação pela rota alterada. Se instalar, isso comprova Appium no provider e elimina pré-requisito de APK universal para essa estratégia de teste, sem criar app.slug. Se falhar, preservar PARTIAL e considerar necessidade de suporte oficial ao driver, sem afirmar item1 concluído.

## LEASE
Um teste de execução no SpawnDroid, owner ChatGPT item1, proibidos canários simultâneos; preflight de /api/sessions barra se qualquer outra sessão ativa. Artefatos e scripts de teste temporários têm path único e são removidos ao terminar. Estado de produção inalterado.
