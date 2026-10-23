# CORTES — pré-lançamento e ACL Windows
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-23
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/185
JOB: Anthares Remote SYSTEM / Windows ACL checks and synthetic regression
COMMIT: 77d18680dbf0b70abf78156a1085cdf2a1eae00a
SUPERSEDES: test-hub/findings/20261023-cortes-isolated-workspace-pilot-partial.md

## Objetivo
Estabelecer workspace protegido, validação pré-lançamento e testabilidade do
isolamento de executores por rede, sem interferir na publicação atual.

## Resultado
Criado grupo local AntharesNetAgents (0 membros) e
D:\AntharesNetworkWorkspaces com herança de ACL desligada:
SYSTEM/Admin FullControl, grupo restrito ReadAndExecute na raiz.
Adicionados ao draft do clipper os módulos network_prelaunch_check.py
e network_acl_attestation.ps1. A fábrica remove agora `origin` do clone.
O prelaunch exige metadados, documentação, SHA, branch, checkout íntegro,
sem remotos Git e comprovação ACL de conta não administrativa.

## Evidência decisiva
Windows Python 3.12: Ran 40 tests ... OK.
PowerShell atestador: PARSER_ERRORS=0; conta ausente => ready=false, exit 3.
ACE deny criada com sucesso somente em diretório temporário de QA;
SANDBOX_DENY_RULE_COUNT=1.
Respostas incertas ao tentar aplicar ACE no root real; reconciliação:
D:\AntharsWork deny-count=0, D:\AntharesWork deny-count=0.
Tentativa de conta/tarefa Windows temporária bloqueada pela segurança
da ferramenta. Readback: probe-user=False, probe-task=False,
pilot_threads=False, pilot_x=False.
Root isolado existe e ACL protegida. Arquivos e publicadores originais
não foram alterados; nenhuma publicação de rede foi iniciada.

## Consequência
Não há isolamento de SO comprovado ainda. Nenhum novo agente deve ser
liberado. A criação de contas/identidades e ACLs do diretório de produção
precisa de mecanismo autorizado e de teste positivo/negativo sob tokens
Windows diferentes. Não contornar o bloqueio de segurança pelo fallback
remoto. Não repetir aplicação de ACL de estado incerto sem reconciliação.
