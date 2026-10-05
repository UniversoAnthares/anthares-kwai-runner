# Histórico antigo do Kwai fechado por quarentena conservadora
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: e69754426a5f149cb63ceb8dac0d2d5300701c9d, 6b15f0ac37effd3f9bad7cadfebfbdcbd081ee51
SUPERSEDES: none

## Objetivo
Impedir que trechos publicados antes da existência do ledger temporal sejam reutilizados.

## Resultado
Foi implementada migração conservadora: toda fonte que já constava em source-history com uso anterior é gravada uma vez em legacy-source-quarantine e sua timeline inteira passa a ser considerada consumida. O seletor exclui essas fontes. O seed remoto legado também recebeu source_id/source_start/source_end.

## Evidência decisiva
Commit e6975442 cria legacy-source-quarantine.json atomicamente a partir do histórico anterior e exclui essas fontes antes da seleção. Commit 6b15f0ac torna o seed legado compatível com o gate temporal.

## Consequência
Fontes antigas de histórico temporal incompleto não voltam à rotação. Perde-se deliberadamente timeline potencialmente inédita dessas fontes em favor da garantia contra repetição. Novas fontes usam reserva temporal exata.
