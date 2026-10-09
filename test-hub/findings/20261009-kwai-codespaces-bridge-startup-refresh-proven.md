# Codespaces command bridge startup refresh is now session-safe
STATUS: PROVEN
AREA: kwai-codespaces-bridge-startup
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37957529967
JOB: browser-only-security
COMMIT: 2c2a2f65afff1c72f93c39465308fd31aa861d59
SUPERSEDES: 20261009-lease-kwai-codespaces-bridge-startup-refresh-1612z.md

## Objetivo
Eliminar o estado em que o Codespace mantém Chrome/CDP vivos mas o command bridge continua executando código antigo após novos commits, sem reiniciar Chrome ou apagar o perfil autenticado.

## Resultado
`.devcontainer/kwai-start.sh` agora localiza somente processos cujo cmdline corresponde a `.devcontainer/kwai-command-bridge.py`, encerra o bridge antigo de forma controlada, inicia uma única instância a partir do checkout atual e deixa Chrome/perfil fora desse ciclo. O postStart do Codespaces já chama `kwai-start.sh`, portanto todo novo start/resume passa a carregar o bridge corrente. O mesmo script pode ser executado manualmente para refresh sem logout.

## Evidência decisiva
- Issue #12 respondeu ao nonce `chatgpt_20261009_profile01` usando o schema antigo (`login_visible`, `profile_link_present`), provando que o processo persistente ainda estava stale apesar de o repositório já conter o verificador estrito.
- Run 37957529967 concluiu SUCCESS no `Kwai Codespaces Browser Security QA` para o commit 2c2a2f65afff1c72f93c39465308fd31aa861d59; o workflow valida parse dos scripts e invariantes de browser privado/loopback.
- O patch não altera nem remove `${HOME}/.kwai-remote-private/chrome-profile` e não reinicia o processo Chrome.

## Consequência
Não repetir Android/Google login para resolver esse problema. Para o Codespace que já estava aberto antes do commit, basta carregar o checkout atual uma vez e executar `bash .devcontainer/kwai-start.sh`; daí em diante o próprio postStart mantém o bridge atualizado em novos starts/resumes. Depois do refresh, repetir `profile_check` e exigir o schema novo (`authenticated_ui_detected`, `own_profile_matches_expected`, `identity_verified`) antes de qualquer publicação.

PEER_CHECK: GitLab main estava em e61d4de6 e não continha `.devcontainer/kwai-start.sh`; nenhuma escrita cega/mirror foi feita no peer.
SECURITY: nenhum cookie, token, senha, credencial, conteúdo de página ou estado de sessão foi exportado.
