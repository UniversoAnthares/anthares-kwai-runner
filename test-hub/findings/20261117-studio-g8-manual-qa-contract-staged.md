# Studio G8 — etapa QA manual preparada

STATUS: PARTIAL
AREA: anthares-studio/g8/manual-qa-contract
DATE: 2026-11-17
OWNER: ChatGPT / OBSERVATORIO IPB
JOB: studio-g8-qa-manual-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/317
COMMIT: ef6db8c94395bbbc448925fc66887c04f9f59060
SUPERSEDES: test-hub/findings/20261117-studio-g8-qa-workflow-running.md

## Implementação
O workflow já existente .github/workflows/anthares-qa.yml recebeu uma etapa de QA do Studio:
- python3 -B -m unittest discover -s anthares-studio/tests -p test_*.py -v
- php -l anthares-studio/anthares-estudio.php
- PHP lint para os arquivos sob anthares-studio/includes
- set -euo pipefail; falhas abortam a etapa.

## Provas
- Diff de arquivos WordPress: a nova versão é a antiga mais exatamente uma etapa de 9 linhas (8/8 contratos estáticos PASS).
- Disparador manual workflow_dispatch preservado; sem push, cron, novas APIs ou chamadas de produção.
- Manifesto QA mantém o caminho existente do workflow; nenhum caminho auditável foi introduzido.
- Nenhum runner, cobrança, deploy ou mutação do banco foi acionado.

## Pendente
A execução hospedada do workflow e a suíte Python integral no HEAD do PR #317 ainda precisam de execução controlada quando a quota e o gate G4 permitirem. G8 permanece PARTIAL, sem homologação final.
