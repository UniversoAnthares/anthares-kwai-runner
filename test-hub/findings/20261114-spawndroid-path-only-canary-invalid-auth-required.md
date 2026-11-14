# Item 1 — canário path-only do SpawnDroid não alcançou o Android (INVALID)
STATUS: PARTIAL
AREA: android|kwai
DATE: 2026-11-14
RUN: none (ARA detached jobs 0beb2ba6433aeab4 e 4d1905b66949a5b8)
JOB: sessão Chromium isolada AntharesSpawnDroid, sem criação de sessão CI
COMMIT: baseline d5f648217899ba4bfd370184006dda0f717e42a7
SUPERSEDES: 20261114-kwai-path-only-spawndroid-canary-running.md
OWNER: ChatGPT item1 / PR #2616

## TEST_VALIDITY
INVALID/NOT_TESTED: o canário usou novo link HTTPS path-only com HMAC que passou GET200, HEAD200, SHA256 correto e assinatura inválida HTTP403. O script temporário preparou 25 URLs mas travou em Playwright connect_over_cdp() antes de consultar /api/sessions e antes de POST /api/v1/sessions. ARA job 0beb2ba6433aeab4 terminou erro de timeout CDP, nenhum resultado de instalação HTTP do path-only. Logo **não concluir sucesso nem fracasso de mobile:installMultipleApks com URL path-only**.
A sessão Chromium foi recuperada usando somente perfil dedicado após confirmar PID/command line; CDP readback passou, mas a página SpawnDroid exigiu login, com redirecionamento Github SSO para https://github.com/login. Não executar credenciais, cookies ou bypass. Login legítimo do titular será necessário.

## Distinção de outra prova
O teste ANTERIOR com URL query (?e=&s=) criou sessão demo real e reportou HTTP500 no comando mobile:installMultipleApks, com terminated_confirmed=true. Essa falha antiga não testa a rota path-only corrigida.
Prova independente de 25 APKs no GitHub OIDC cloud foi fechada como PROVEN pelo run 43641732854, com apksigner oficial, sem sessão SpawnDroid.

## Consequência
Aguardar sessão SpawnDroid autorizada ou chave de API oficial de escopo mínimo, quota e slot conferidos antes de um único canário Android. Não reenviar posts; cloud_cutover.enabled=false. O script temporário do canário foi preparado em D:\AntharsWork\spawndroid-preflight-qa\kwai_ci_install_canary_pathonly_temp.py; como o job saiu antes da limpeza prevista, verificar a existência e apagar apenas esse arquivo de propriedade do canário, preservando artefatos e logs de QA.
