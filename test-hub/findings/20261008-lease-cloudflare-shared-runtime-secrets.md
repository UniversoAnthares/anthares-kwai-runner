# Lease: shared runtime secrets architecture
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Implementar arquitetura em que Cloudflare/control plane seja a fonte independente de segredos operacionais para workloads portáveis entre GitHub e GitLab, evitando duplicação manual de secrets e dependência de GitHub Actions para failover.

## Baseline
GitLab hosted execution de Clipper/WordPress já foi comprovada para validação de código. Clipper produtivo permanece bloqueado por credenciais runtime ausentes no GitLab.

## Evitar
Não recriar mirror CI legado, GITLAB_MIRROR_URL, nem expor/copiar valores secretos para Git, logs ou Test Hub. Não afirmar failover produtivo até teste real.

## Aceitação
Código/control plane deve falhar fechado, autenticar executor, não retornar secrets em endpoints públicos/logs e permitir consumo efêmero por executor autorizado.

## Lease
Owner: current ChatGPT agent. Expira em no máximo 30 minutos; renovar antes de novas mutações se necessário.
