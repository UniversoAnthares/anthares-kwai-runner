# Lease: metadados universais e habilitação Pinterest/LinkedIn
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-20
RUN: none
JOB: none
COMMIT: d27ae41750f5265a04b80e3431b26ae0e73dde7c
SUPERSEDES: none
LEASE_AREA: cortes-social-pinterest-linkedin-editorial
LEASE_OWNER: chatgpt-current-conversation
LEASE_MAX_EXPIRY_UTC: 2026-10-21T00:35:00Z

## Objetivo
Criar regras editoriais idempotentes para sufixo de título « ● Universo Anthares» e referência www.anthares.us nos campos textuais apropriados, trocar Pinterest para publicação de todos os cortes elegíveis da rodada, preservar LinkedIn com limite de 20 por dia e preparar adaptadores de vídeo oficiais para os dois destinos.

## BASELINE_PROVEN
GitHub main d27ae41750f5265a04b80e3431b26ae0e73dde7c. Media model e patch target-v17 ainda definem pinterest:20 e linkedin:20. Social adapter atende somente Instagram, Threads e X. GitLab main 4f4a6fa7cc812f87609dc1373a30a80392d60d87 contém merge do mesmo commit; histórico GitLab independente.

## FAILED_AVOIDED
Evitar tentativa de postagem como probe sem token/permissões, post duplicado sem ledger, deploy de origem v16 diretamente sobre versão mais recente, alteração concorrente em main, ou repetição de acesso OAuth sem evidências.

## SUCCESS_SIGNAL
Mudanças isoladas numa branch, revisão, compilação e testes unitários sem credenciais reais; publicação real só quando identidade, token, limites de API, confirmação remota e ledger estiverem comprovados.

## FAILURE_SIGNAL
Testes falham, SHA concorrente altera arquivo alvo, conflito de lease ou autenticação insuficiente. Neste caso interromper o write/publish sem fallback cego.

## TEST_VALIDITY
Testes com mocks determinísticos sem acesso a contas reais; sucesso de CI equivale somente a validação estática. Integração live exige prova separada de publicação remota.

## Situação
Lease registrado antes de mudanças. Nenhuma publicação efetuada como teste.
