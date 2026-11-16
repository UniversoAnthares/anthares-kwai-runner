# Anthares Studio — proposta de registro G0 e coordenação documental
STATUS: PARTIAL
AREA: studio-documentation
DATE: 2026-11-16
RUN: nenhuma execução de código
JOB: proposta de PR para documentação
COMMIT: none
SUPERSEDES: none

## Baseline
- Código original: plugin `anthares-estudio` 0.7.7 em /estudio/, SHA-256 do PHP original `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.
- /estudio/ HTTP 200 e diretório /studio/ plugin ausente, revalidados em 16/11.
- GitHub anthares-wordpress/main: `808d2968f8a869ff32b95c59ab356d370d3732e9`, ainda sem plugin original e sem documento de handoff oficial.
- Dossiê documental G0 preparado com 19 arquivos e matriz de 188 requisitos; sem implantação ou migração nesta etapa.

## FAILED_AVOIDED
- Não recriar interface do zero.
- Não copiar `aest_*` sem isolamento.
- Não expor CPTs privados por `public=true`.
- Não utilizar o antigo PR #275 como fonte atual do legado.
- Não iniciar cópia de dados sem reconciliar registros `anst_*` possivelmente remanescentes da migração de 15/11.
- Não editar `anthares-estudio` em produção.

## SUCCESS_SIGNAL
- Documentação anexada em branch/PR exclusiva de `anthares-wordpress`, com SHA e manifestos QA consistentes.
- Revisão e aprovação do contrato de isolamento e do plano G0–G8.
- Novo finding posterior de gate aprovado, com link à revisão e lease para o gate seguinte.

## FAILURE_SIGNAL
- Divergência com governança ou contrato aprovado; ausência de dados de migração; QA manifesto divergente; conflito entre agentes.

## TEST_VALIDITY
Somente leitura e conferência documental; sem teste funcional novo e sem mutação do WordPress.

## Estado e consequência
Esta PR **é proposta de coordenação**, não lease ativo nem aprovação G0. O Test Hub não admite escrita direta na branch `main`; qualquer registro definitivo exige PR. Antes de operar G1/G2, adquirir lease apropriado, confirmar ausência de mutações concorrentes e registrar aprovação/handoff com evidências.
