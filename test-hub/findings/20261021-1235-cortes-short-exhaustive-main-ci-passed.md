# CORTES — transcrição para descarte e plano exaustivo de curtos
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-21
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/39600488373
JOB: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/39600488373/job/119223439781
COMMIT: 2663646275a2aa8eac3e2df4b125e44a2ee72bcc
SUPERSEDES: test-hub/findings/20261021-lease-cortes-short-exhaustive-discard-only.md

## Objetivo
Aplicar pedido do proprietário: sem quantidade mínima de curtos e sem filtro de notas. Ler a transcrição somente para descartar trechos dispensáveis; produzir todos os cortes tecnicamente viáveis no restante; manter microedições, duração final 30–90s e layout 9:16.

## Resultado
PR https://github.com/UniversoAnthares/anthares-clipper/pull/105 integrado à GitHub main com commit 2663646275a2aa8eac3e2df4b125e44a2ee72bcc. O modulo cortes_short_exhaustive.py classifica apenas descartes via AI Hub, salva checkpoints por janela e particiona todo o restante em candidatos sem notas ou teto de quantidade. cortes_short_batch.py preserva masters anteriores, elimina truncamento por 100, cutoff diário e ranking editorial. O guard de retomada passa a aceitar cobertura incompleta e novas listas maiores.

## Evidência decisiva
Python 3.12 isolado no Windows: compilação e 31 testes passaram (6+2+11+10+2). Simulação de 3 horas sem descartes resultou em 270 candidatos, apenas para demonstrar ausência de teto. GitHub Actions CORTES Python CI run 39600488373 concluiu SUCCESS em sintaxe, checkpoints, politica de duracao, access policy e layout.

## Limitações
Nenhuma rodada real foi disparada; a rodada de 21/10 não foi refeita. GitLab fallback run 39600488374 falhou independentemente do CI principal; GitLab main tem histórico divergente e não foi espelhado. A próxima rodada automática utiliza a main nova se o runner checkout e as dependências reais estiverem disponíveis. Teste sintético não demonstra 270 MP4 reais.

## Consequência
Lease encerrado nesta área. Para comprovar volume efetivo de cortes, consultar logs de execução e ledger de media.
