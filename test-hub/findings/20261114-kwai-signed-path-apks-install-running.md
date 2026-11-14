# Item 1 — URL assinada terminada em .apk para Appium remoto
STATUS: RUNNING
AREA: android|kwai
DATE: 2026-11-14
RUN: none
JOB: Hostinger .htaccess roteamento alternativo HMAC; PR #2616
COMMIT: 6722a4310662ba71fed360a791ac70c804f9d0b2
SUPERSEDES: none
OWNER: ChatGPT item1 branch feature/spawndroid-kwai-apk-verified-upload-20261114
GOVERNANCE_RULES_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138

## BASELINE_PROVEN
- Hostinger privado contém 25/25 APKs com SHA256 correto (202108730 bytes), verificação independente real de assinatura v2 e digest completa para todos os 25 realizada por tools/kwai_apksig_v2_audit.py, exit 0.
- GET assinado com query (?e=&s=) responde 200 e SHA256 correto; requisição HEAD assinada com query responde 200.
- Canário Android anterior de 14/11 criou sessão demo sess_4139ebebc97647c894, tentou mobile: installMultipleApks com 25 URLs da forma /nome.apk?e=&s=, recebeu HTTP 500 unknown error, sessão encerrada com confirmação. Sem publicação/login.
- Driver Appium exige itens terminados em .apk, embora documentação admita URLs; hipótese nova: a extensão aparente para cada valor passado ao driver é .apk?e=&s=, que pode ser rejeitada por validação de caminho/URL.
- Hostinger .htaccess original SHA256 8199b73c6eecf6e70a85c42c4c9082b0d1723f6997e2ea3ec0cf090197c1ae50 e contém regra original de rewrite para /filename.apk; fetch.php mantém HMAC e leitura restrita.

## FAILED_AVOIDED
Não repetir exatamente o canário com query original; não alterar fetch.php/HMAC; não expor segredo ou emitir URL sem assinatura; não iniciar Android sem verificar cota/slot e TestHub. Preservar URL antiga, backup e publicadores.

## SUCCESS_SIGNAL
Criar rota adicional opcional /signed/<expiry>/<signature>/<filename>.apk no .htaccess, mapeada internamente para fetch.php?f=...&e=...&s=..., com HMAC original sem mudanças; teste real GET/HEAD 200 e SHA256 válido, token adulterado 403. Preservar regra antiga, segredo e demais serviços.

## FAILURE_SIGNAL
Qualquer erro 500/403 em caminho corretamente assinado, URL antiga deixa de funcionar, 5xx do site, hash divergente, SSL inválido; rollback imediato do .htaccess via backup privado.

## TEST_VALIDITY
Prova do novo roteamento HTTPS é independente de Appium. Somente iniciar novo canário Android depois de comprovar rota e consultar slot/quota, com diagnóstico de erro seguro e idempotência; evitar atribuir sucesso sem app instalado/readback.

## LEASE/PEER
Alterar exclusivamente .htaccess da pasta staging Hostinger; não alterar fetch.php; backup privado antes de mv atômico. Local staging.htaccess e regra no repo verificados para reconciliação. Agentes 01–07 não editam este caminho no momento; se HEAD alterar, abortar.
