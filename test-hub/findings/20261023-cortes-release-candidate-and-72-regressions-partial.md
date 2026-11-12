# CORTES — entrega independente por rede e 72 testes de regressão
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-23
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/185
JOB: Anthares Remote / seis suítes Python 3.12 / staging isolado
COMMIT: bf83a213d9a62fa34cc6496b787198294002e875
SUPERSEDES: test-hub/findings/20261023-cortes-network-export-no-foreign-git-objects-partial.md

## Objetivo
Exigir propriedade exclusiva de arquivos por rede também na preparação
de um pacote de release, antes do deployment; endurecer preflight documental.

## Resultado
ci/network_release_candidate.py gera ZIP de revisão apenas com paths
aprovados pela admissão de uma rede, com hashes SHA256 por arquivo, SHA
do arquivo final, documentação validada, origem e base imutável.
Não aceita alterações cruzadas, symlinks, exclusões, arquivos sensíveis,
destino dentro do workspace ou sobrescrita de ZIP já existente.
Manifesto marca deployment_allowed=false e review_required=true.
ci/network_change_admission.py agora confere diretamente os hashes dos
documentos locais do workspace, além de invocar policy.py preflight.

## Evidência decisiva
Primeira suíte de release: 8/9 PASS; teste de documento adulterado revelou
ausência de verificação independente quando policy.py era substituído por
fixture permissiva. Correção causal aplicada ao módulo de admissão e fixture.
Novo teste isolado do ZIP: Ran 9 tests ... OK.
A execução conjunta via Anthares Remote retornou estado incerto sem
recibo final. Foi verificado que o processo encerrou, mas sem resultado.
Reexecutadas por arquivo, com logs e exit-code 0 em cada grupo:
- test_network_scope_guard.py: 14 PASS
- test_network_change_admission.py: 14 PASS
- test_network_agent_launch_contract.py: 12 PASS
- test_network_workspace_factory.py: 13 PASS
- test_network_workspace_export.py: 10 PASS
- test_network_release_candidate.py: 9 PASS
TOTAL: 72 PASS, nenhuma falha, nenhum skip nesta rodada.

## Consequência
STATUS PARTIAL: PR #185 somente draft. O pacote ZIP não é assinado,
implantado nem autoriza o publicador a operar. A independência em runtime
ainda aguarda identidades Windows/ACL comprovadas, credenciais por rede,
filas/ledgers segregados, broker e release controller protegido.
Não contornar a recusa da ferramenta à criação de contas Windows.
