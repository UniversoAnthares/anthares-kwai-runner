# APKMirror universal 2024 — download cloud bloqueado com HTTP 403
STATUS: FAILED
AREA: android|kwai
DATE: 2026-11-14
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43623204183
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43623204183/job/132533238594
COMMIT: 0f45a16f5778cf22083b11555bfbe782d81abe08
SUPERSEDES: 20261114-apkmirror-official-universal-archival-canary-running.md
OWNER: ChatGPT item1 / PR #2616

## Resultado
GitHub-hosted Ubuntu realizou uma tentativa única de download normal da ficha de APK individual Kwai 10.6.10.536002, pacote com.kwai.video, tamanho publicado 255956802 bytes, hash de referência 76e6a6208f3979e0e6e69807160d7fe9d3b0ef97c82f6980933eb775616b4b58. A primeira leitura remota da página pelo Python do runner recebeu HTTP 403: Forbidden. O processo encerrou com exit 1.

## Evidência decisiva
Run 43623204183, job 132533238594: `urllib.error.HTTPError: HTTP Error 403: Forbidden`, no passo `Download original APK through public APKMirror links`. Nenhum arquivo binário legítimo obtido e nenhum hash/apksigner real executado; sem upload API, app.slug, sessão Android ou publicação.

## Consequência
HTTP 403 é restrição de acesso, não falha de quota; não repetir a mesma tentativa com outro canal para evitar o controle de acesso. Workflow temporário `.github/workflows/kwai-apk-archive-oneoff.yml` deve ser retirado do PR após confirmação deste finding. Buscar outra distribuição legitimamente acessível ou priorizar original splits via Appium sob prova de suporte. A versão 2024 teria risco relevante de incompatibilidade de login/publicação em 2026. Manter cloud_cutover.enabled=false e publicadores atuais.
