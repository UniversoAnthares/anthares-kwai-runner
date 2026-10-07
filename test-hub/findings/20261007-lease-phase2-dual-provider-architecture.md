# 2026-10-07 — Lease phase 2 dual-provider architecture

STATUS: RUNNING
AREA: architecture/provider-router
DATE: 2026-10-07
RUN: none
JOB: none
COMMIT: d325de6a532cb1841348c3a12ecc457a9fa5e1e8
SUPERSEDES: none

## Objetivo

Implementar a primeira camada executável da arquitetura neutra entre GitHub e GitLab: seleção de provider, health/quota, lease, checkpoint e failover sem autoridade permanente de nenhum Git.

## BASELINE_PROVEN

- anthares-control é o plano de controle central existente e já possui lease/heartbeat/fencing.
- GitHub e GitLab são provedores disponíveis, mas o GitHub privado está temporariamente bloqueado por cota de Actions.
- O GitLab possui integração operacional nesta sessão.
- Não existe autorização para dois executores concorrentes na mesma operação.

## FAILED_AVOIDED

- Evitar assumir GitHub ou GitLab como autoridade permanente.
- Evitar failover enquanto o primeiro executor ainda possui lease ativo.
- Evitar executar contra um provider cujo HEAD/checkpoint não foi verificado.
- Evitar duplicação do control plane.

## SUCCESS_SIGNAL

- Código versionado fornece estado normalizado de providers.
- Seleção escolhe provider disponível sem preferência estrutural.
- Lease impede dupla execução.
- Checkpoint permite verificar continuidade antes do failover.
- Testes unitários cobrem seleção, bloqueio por lease, divergência e failover.

## FAILURE_SIGNAL

- Dois providers selecionados para a mesma operação.
- Failover aceito com checkpoint divergente.
- Provider indisponível selecionado.
- Lease expirado/revogado ainda aceito.

## TEST_VALIDITY

Os testes são determinísticos e locais ao módulo de roteamento; nenhum sucesso depende de GitHub Actions, GitLab CI, Android/KVM, credenciais ou serviços externos.

## Expiração

Máximo: 30 minutos.

## Regra

Durante este lease, mutações da cadeia architecture/provider-router ficam serializadas. Não alterar kwai-login, kwai-publish, queue ou cloudflare-control.
