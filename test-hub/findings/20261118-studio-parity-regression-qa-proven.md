# Studio — paridade 5x7 e QA da PR #326
STATUS: PROVEN
AREA: anthares-studio/parity/qa
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-parity-20261118
RUN: Hostinger SSH, checkout isolado
COMMIT: b14bdaec0145095babf3e6372eeef4fc6d0bae9b
PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/326
SUPERSEDES: test-hub/findings/20261118-studio-parity-regression-running.md

## Objetivo
Corrigir regressões verificadas em PR #321 sem modificar legado ou produção. Validar menu de cinco entradas, testes G6, CSS e lixeira.

## Evidência decisiva
- Branch baseada em PR #321, com quatro arquivos modificados.
- Testes Python **91/91 PASS** (0 falhas).
- PHP 8.3: **lint PASS**.
- Manifesto QA: **676/676 PASS**, exactly_once=yes.
- Orquestrador QA: **11/11 PASS**.
- Clone temporário Hostinger removido, CLEANUP=0.
- Diff produção versus branch: JavaScript idêntico; PHP do destino já continha tratamento seguro de projeto na lixeira; diferenças do CSS são finais de linha.
- Alteração de código ficou na PR draft #326; nenhuma operação de escrita REST nem alteração de dados do WordPress.

## Limites
Esta prova se refere ao código. End-to-end autenticado, desktop/mobile, permissão WordPress real, deploy e reconciliação G4/G5 permanecem sujeitos aos gates já documentados. PR DRAFT sem merge automático.