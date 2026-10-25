# SEC-02 — lease independente: teste de duas identidades reais de banco em QA
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-25
RUN: none
JOB: r07-sec02-20261025
COMMIT: base main 183f6a8eda4d2585f6cdd73982984a66df541802
SUPERSEDES: none

## BASELINE_PROVEN
No Neon main há apenas um usuário provider-managed neondb_owner e ausência de RLS em cortes_publications; o ramo QA compartilhado possui roles NOLOGIN, insuficientes para comprovação de identidades autenticadas independentes. Preflight local f6fc9ca59a96e451 PASS, audit 218/0.

## FAILED_AVOIDED
A tentativa anterior de criar ambiente GitHub exclusivo para TikTok foi recusada por controle de segurança. Não repetir nem contornar essa criação em outro canal. Bitwarden SDK de inventário falhou autenticando no ensaio 39511953159; não repetir com bootstrap idêntico. Não obter, exportar ou revelar credenciais. Sem alterar filas, dados e publicadores reais.

## SUCCESS_SIGNAL
Em branch QA Neon criada exclusivamente para esta auditoria: dois papéis LOGIN gerenciados pelo provedor com nomes diferentes, permissões apenas em objetos sintéticos de cada rede e consultas que comprovem ALLOWED para si e DENIED para outro papel; verificações como cada papel conectado por credencial própria interna do conector, sem valores retornados.

## FAILURE_SIGNAL
Uso de papel administrador como identidade da rede, acesso cruzado concedido, RLS burlada, operação de produção ou teste em branch compartilhada.

## TEST_VALIDITY
Testar SQL com role_name distinto em branch identificada; não inferir controle da rede social a partir de privilégios SQL. Nunca declarar SEC-02 concluído em produção por resultado de QA.

## SCOPE
Novos recursos isolados em branch do banco QA com prefixo sec02_, findings append-only em branch GitHub exclusiva; sem merge e sem deploy. Lease válido até 2026-10-25T22:05Z ou 30 minutos, o que ocorrer primeiro.
