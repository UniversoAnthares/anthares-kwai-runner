# CORTES — exportação de Git limitada à rede e contratos Kilo/Claude/Codex
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-23
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/185
JOB: Anthares Remote / Python 3.12 / staging D:/AntharesNetworkWorkspaces/_qa_20261023_launch
COMMIT: 10a17170b62af3b935f3755de536fee0d2644ebb
SUPERSEDES: test-hub/findings/20261023-cortes-windows-acl-prelaunch-partial.md

## Objetivo
Eliminar exposição de commits e objetos de outras redes num workspace
de um agente; criar contratos Kilo, Claude e Codex sem executar os agentes.

## Resultado
Implementado ci/network_workspace_export.py: cria um Git independente de
uma única rede, copia exclusivamente arquivos versionados em networks/rede,
docs/networks/rede e tests/networks/rede. Não copia a base de objetos Git.
Registra SHA de origem e novo SHA local, sem remote, bloqueia symlink
versionado, caminhos sensíveis e conteúdo acima dos limites definidos.
Implementado ci/network_agent_launch_contract.py: prende rede, job, dono,
conta e binário a controller binding; recusa ausência de prelaunch e cria
planos argv sem executar. Recibos omitem prompt, stdin e comando.

## Evidência decisiva
Windows/Python 3.12: Ran 62 tests ... OK. Testes sintéticos positivos
para Kilo, Claude e Codex sem subprocess de agentes.
Smoke na fonte CORTES local SHA
1b38db5829c8c1235ff3080c3c73edb1ec270903:
exportação Threads pronta, gov=898630c1c5143f34,
EXPORTED_COMMITS=1, EXPORTED_REMOTES=0,
FOREIGN_KWAI_BLOB_CATFILE_RC=1,
SOURCE_HEAD_AND_CHANGES_PRESERVED=True, STAGING_REMOVED=True.
Primeiro smoke usou caminho social_api_publisher.py ausente naquela SHA;
abortou antes de exportar e limpou staging. Novo smoke selecionou
kwai-up/kwai_up.py, comprovadamente presente, e terminou com êxito.

## Consequência
STATUS continua PARTIAL. Somente PR draft. Nenhum publicador, launcher
Kilo/Claude/Codex ou segredo de produção alterado. O isolamento real de
processos ainda depende de conta/ACL, broker, proteção de deploy e
separação de filas/ledgers. Não contornar bloqueio da ferramenta a
provisionamento de contas Windows por outro canal.
