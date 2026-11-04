# Lease — registrar prova da restauração integral sem escrita e controles ativos
STATUS: RUNNING
AREA: architecture
DATE: 2026-11-04
RUN: none
JOB: existing Neon read-only query / isolated Code Mode validation
COMMIT: 909d658732878a477d22118a800a0f35fb2a3ee0
SUPERSEDES: none
LEASE_OWNER: ChatGPT / Reestruturação e Otimização / CORTES
LEASE_START_UTC: 2026-11-04T03:43:17.369Z
LEASE_EXPIRES_UTC: 2026-11-04T04:03:17.369Z
GOVERNANCE_MANIFEST: 223433740e807a90

## BASELINE_PROVEN
- Clipper main 52987aed165f3682ef6c5f5ec0774b76bad94893 contém o leitor Python de QA e nove testes sintéticos; gatilho GitHub-hosted permanece inativo.
- Banco Neon já guarda duas revisões verificadas, a maior 15399 (2932006 bytes, digest prefixo cc5d1a18). Não criar novos jobs/projetos/segredos, nem escrever na produção.
- PR Clipper #229 de CAS/escritor único está DRAFT e pertence a outro fluxo. Não alterar seu código, migrações ou serviços.

## FAILED_AVOIDED
- Sem PC como runner ou staging; sem uploads, publicações, cobrança, retenção local ou ativação do writer.
- Uma consulta agregada específica encontrou recusa de segurança; DENIED_PENDING_REVIEW, sem repetição nem ferramenta alternativa.

## SUCCESS_SIGNAL
- Finding reproduzível com recuperação integral dos bytes, SHA256 externo, contagem de fontes/segmentos, limites da ferramenta e diagnóstico do controle por consultas SELECT, sem divulgar dados privados.
- Registro de limites de aceite do runner original e da PR de fencing.

## FAILURE_SIGNAL
- Divergência SHA, perda de lease/fence de outro agente, segredo revelado, disparo de workflow ou tentativa de escrita.

## TEST_VALIDITY
Este lease é exclusivo para registro de evidência de leitura já observada e atualização do índice. Não autoriza alterar a operação CORTES. Encerra-se por finding na mesma PR.
