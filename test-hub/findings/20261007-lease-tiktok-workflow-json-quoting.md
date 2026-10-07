# Lease — correção de quoting JSON nos workflows TikTok
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-07
RUN: none
JOB: MDE9nE00YIndrW2UFftCo3
COMMIT: pending
SUPERSEDES: none
EXPIRES: 2026-10-07T16:15:00Z

## Objetivo
Corrigir somente a serialização dos payloads JSON enviados por `curl` nos workflows TikTok, sem disparar workflow, publicar, reconciliar ou chamar o control plane.

## BASELINE_PROVEN
A auditoria local reproduziu a expansão de `--data "{...}"` para JSON sem aspas de propriedades/valores em Bash.

## FAILED_AVOIDED
Não executar os workflows, não alterar tokens OIDC, não mudar IDs/dedupe/contratos de fila e não criar novo canário.

## SUCCESS_SIGNAL
Cada payload é gerado por `json.dumps`, chega ao `curl` em uma variável sem token na string, e a validação offline de YAML/trechos confirma JSON válido para os campos estáticos/dinâmicos.

## FAILURE_SIGNAL
Qualquer `--data "{"` inseguro permanece nos arquivos-alvo ou o patch muda a semântica do job.

## TEST_VALIDITY
Somente inspeção local, parsing/geração JSON com valores sintéticos e validação de shell; nenhuma URL externa será acessada.
