# Correção OIDC implementada; deploy privado continua inválido
STATUS: PARTIAL
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/37387751488
JOB: 112025248903
COMMIT: 8fa4187db1316f11bc8f0213e410dd800f1cc886
SUPERSEDES: test-hub/findings/20261005-1917-lease-cloudflare-control-tiktok-read.md

BASELINE_PROVEN: OIDC GitHub já é criptograficamente validado; Worker atual mantém issuer/audience/repository/ref/event/signature e allowlist por workflow.
FAILED_AVOIDED: não interpretar falha do runner/deploy como falha da hipótese OIDC; não rerodar o mesmo deploy privado.
SUCCESS_SIGNAL: tiktok-central-session-read recebe /tiktok/session-state sem 401 após deploy confirmado.
FAILURE_SIGNAL: 401 jwt_workflow após deploy confirmado da versão 8fa4187 ou posterior.
TEST_VALIDITY: run de deploy precisa executar Wrangler e confirmar versão ativa; falha imediata sem logs é falha do mecanismo de deploy.

## Objetivo
Autorizar somente o workflow público de leitura central TikTok sem afrouxar as demais validações OIDC.

## Resultado
Código do controlador foi atualizado para incluir tiktok-central-session-read.yml na allowlist. O push disparou automaticamente o workflow privado Anthares Cloudflare Deploy Once, run 37387751488, que terminou failure imediatamente; logs indisponíveis. É o mesmo padrão causal do finding 20261005-2247-cloudflare-private-runner-failed e não testa o código novo.

## Evidência decisiva
Commit 8fa4187 contém a allowlist nova. Run 37387751488/job 112025248903 = failure; mecanismo de logs indisponível. Nenhuma evidência de deploy efetivo foi produzida.

## Consequência
Não repetir deploy pelo runner privado. Próxima tentativa deve mudar causalmente para runner público/hub. A hipótese OIDC permanece não testada em produção.
