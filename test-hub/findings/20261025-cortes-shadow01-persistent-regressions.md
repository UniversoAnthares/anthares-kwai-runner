# CORTES SHADOW-01 — regressões permanentes do auditor de pré-migração
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-25
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/202
JOB: ARA qa-shadow01-20261025 / Testes Python Windows
COMMIT: d87118e2cb844369bcf7a9341624b7ef83454d29
SUPERSEDES: none

## Objetivo
Concluir a lacuna de cobertura persistente do auditor offline `ci/network_shadow_cutover.py`, preservando a proibição de cortar para um novo publicador sem atestar os gates operacionais.

## Preflight e isolamento
Governança local aprovada em revisão f6fc9ca59a96e451; versões locais e GitHub da governança permanecem divergentes e foram preservadas. Código-base consultado no GitHub main, SHA 2084019a95cfa04560866bb3a18722e92344771f. Ensaios realizados exclusivamente em diretório QA isolado `D:\AntharsWork\qa-shadow01-20261025`, com três módulos existentes do main e snapshots fictícios. Nenhuma fila real, segredo, perfil, SQL ou publicador foi acessado pelo teste.

## Resultado
Adicionado `tests/test_network_shadow_cutover.py` ao `UniversoAnthares/anthares-clipper/main` pela PR #202, merge squash d87118e2cb844369bcf7a9341624b7ef83454d29. Readback de main confirmou 27 métodos de teste; blob GitHub aa80ffd09eeff5f2e16b0b4987827de70cea6b0e.

## Evidência decisiva
Execução Windows/Python 3.12.10: `py -m unittest discover -s tests -p test_network_shadow_cutover.py -v`; saída `Ran 27 tests in 0.252s`, `OK`, exit code 0. Log local 4193 bytes; SHA-256 7236394c81062cea6c94d5aff2a6b3df7ca960332bf4842ba455898409a6bc4a. Abrange snapshots válidos/inválidos, estado STARTED/UNCERTAIN, secret fictício, identidade de outra rede/conta, duplicatas, metadados ausentes, CLI e invariantes de bloqueio de ativação.

## Limitações
Validações independentes da proteção SQL/RLS, IAM, ACLs Windows, secret segregation, single writer e prova externa continuam obrigatórias. A suíte offline deliberadamente retorna `cutover_authorized=false` e `deploy_authorized=false`; não constitui autorização de implantação/publicação nem homologação E2E. O workflow de Shorts disparado pelo PR foi validação CI/dry-run e terminou SUCCESS; ele não substitui esta execução específica de 27 testes.

## Consequência
SHADOW-01 (persistência e regressão fail-closed de auditor) CONCLUÍDO na camada de QA de código. Programa de migração e isolamento permanece PARCIAL até as provas reais de identidades, RLS, writer único, recibos e canário autorizados. Nenhuma alteração ou promoção de publicadores foi feita.
