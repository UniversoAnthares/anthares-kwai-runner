# CORTES — clone esparso por rede e admissão real Threads/X
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-23
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/185
JOB: Anthares Remote SYSTEM, Windows Python 3.12, smoke de clone local em TEMP
COMMIT: 7e8730d1f4edddacf376590ff19dd24c83b81d43
SUPERSEDES: test-hub/findings/20261023-network-isolation-admission-partial.md

## Objetivo
Comprovar workspaces Git independentes, sparse checkout por rede e bloqueio
por rede antes de integrar lançadores e implantações.

## Resultado
`ci/network_workspace_factory.py` cria clone independente a partir de SHA
fixado. Usa sparse checkout (apenas networks/<rede>, docs/networks/<rede> e
tests/networks/<rede>); valida documentação central, preserva workspace
existente e limpa clone novo incompleto inclusive read-only Windows.
Endurecido `network_scope_guard.py`: mudanças de controle compartilhado
precisam de branch `platform/<job>` e revisão separada.

## Evidência decisiva
35 testes executados via Anthares Remote em Windows/Python 3.12: todos PASS.
Smoke real a partir do Git local do CORTES (HEAD 1b38db5829c8c1235ff3080c3c73edb1ec270903):
fábrica retornou governança 898630c1c5143f34, deploy_authorized=false;
um arquivo fictício em networks/threads/pilot.py passou admissão;
um arquivo fictício em networks/x/forbidden.py foi recusado.
Workspace temporário excluído: TEST_ROOT_REMOVED=True.
Nenhum script de publicação, serviço Windows, perfil de navegador, fila
Neon, token ou arquivo de produção foi modificado nesse teste.

## Limites
STATUS permanece PARTIAL: PR draft, sem integração ao lançador/CI de produção.
Git object storage do clone contém histórico completo da origem; ainda
faltam segregação por repositório/identidade, ACL de SO, executor,
credenciais e releases. Agente com permissões amplas no mesmo Windows
pode contornar um verificador local; criar fronteira de confiança de SO.
