# Lease — Kwai stale PID recovery
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-10
RUN: none
JOB: none
COMMIT: a6aed00d505342f2538c2dec52b460a8970bcd10
SUPERSEDES: none

## Objetivo
Corrigir a inicialização pós-stop/start do Codespace sem tocar no perfil persistente do Chrome, tratando PID files persistentes que podem apontar para PIDs reutilizados por processos não relacionados.

## BASELINE_PROVEN
- Codespace supreme-spork-x4gpgwv5x7xfv55j está Available e checkout main está ahead=0/behind=0.
- Stop/start foi executado após o merge do recovery orchestrator, mas a issue #12 continuou sem resposta.
- `.devcontainer/kwai-start.sh` considera qualquer PID vivo em pidfile como processo correto; `restart_current_bridge` aborta se bridge.pid aponta para um PID vivo cujo cmdline não é bridge.

## FAILED_AVOIDED
- Não repetir apenas stop/start sem mudança causal.
- Não reconstruir o container nem apagar `$HOME/.kwai-remote-private/chrome-profile`.
- Não matar PID cujo cmdline não corresponde ao serviço esperado.
- Não publicar conteúdo real.

## SUCCESS_SIGNAL
Após patch e novo stop/start não destrutivo: comando `KWAI_BRIDGE_CMD inspect <nonce>` recebe `KWAI_BRIDGE_RESULT` novo; em seguida `profile_check`/`owner_probe` retornam os sinais de autenticação/identidade exigidos.

## FAILURE_SIGNAL
Bridge continua silenciosa depois que pidfiles stale deixam de bloquear os serviços, indicando causa distinta.

## TEST_VALIDITY
Patch passa `bash -n`; somente resultados novos da issue #12 contam como evidência runtime. Falha do harness não será interpretada como falha da sessão Kwai.

## Lease
Área: kwai-login. Expira em no máximo 30 minutos. Nenhuma publicação real é autorizada.