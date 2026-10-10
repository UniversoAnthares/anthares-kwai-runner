# Lease renewal — Kwai bridge recovery orchestrator
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38053581918
JOB: 114217439150
COMMIT: 0c01a40552e9d718a8a5e8d7c8494d83b64c2163
SUPERSEDES: 2026-10-10-lease-kwai-bridge-recovery-orchestrator.md

## Objetivo
Corrigir o canal autônomo de recuperação após evidência real: GitHub Actions executa, Cloudflare está READY, mas o token do workflow não possui escopo Codespaces e a bridge owner-only ignora comandos emitidos por github-actions[bot].

## BASELINE_PROVEN
- GitLab pipeline 2933485525 / job 17080504529: executor remoto READY, Cloudflare v12 saudável, issue #12 observável.
- GitHub Actions run 38053581918: workflow executa; Codespaces API retorna 403 com GITHUB_TOKEN; Cloudflare READY; identidade não comprovada.
- Comentário GitHub Actions 6097699180 é user=github-actions[bot] e performed_via_github_app.slug=github-actions.
- AI Commander registra aic-kwai-codespace como OFFLINE.

## FAILED_AVOIDED
- Não depender de noVNC.
- Não usar o PC como executor de produção.
- Não aceitar genericamente qualquer bot na bridge.
- Não publicar sem identity_verified=true.
- Não tratar 403 de autorização como falha da sessão Kwai.

## SUCCESS_SIGNAL
A bridge aceita somente OWNER ou comandos estritamente identificados como GitHub Actions oficial do repositório, processa nonce novo após recuperação, e profile_check/owner_probe retornam chrome_connected=true, authenticated_ui_detected=true e identity_verified=true para @lucasrosalem.

## FAILURE_SIGNAL
Codespace continua indisponível após autorização lifecycle válida ou bridge não responde depois de reiniciada.

## TEST_VALIDITY
Autorização Codespaces, inicialização do Codespace, confiança do comando, conexão Chrome e identidade são sinais separados. Falha de uma camada não é inferida como falha das demais.

## Lease
Área: kwai-login. Expira em no máximo 30 minutos a partir deste finding. Nenhuma publicação real é autorizada por este lease.
