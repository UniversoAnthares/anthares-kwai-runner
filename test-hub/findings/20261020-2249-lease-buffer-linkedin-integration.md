# Lease: adaptador Buffer LinkedIn da conta Anthares
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-20
RUN: none
JOB: none
COMMIT: 2e49451e3ce1a16728ab25b3848f6c432cad1679
SUPERSEDES: none
LEASE_AREA: cortes-buffer-linkedin-adapter
LEASE_OWNER: chatgpt-current-conversation
LEASE_MAX_EXPIRY_UTC: 2026-10-21T04:30:00Z

## BASELINE_PROVEN
Buffer autenticado no browser do proprietário, publish.buffer.com/home com 0/3 canais conectados. API GraphQL pública da Buffer confirmada nas docs oficiais. A janela do proprietário não pode ser controlada pelo conector Browser (somente leitura); WinRemote caiu com tunnel-client offline; Anthares Remote desktop bloqueado com owner authorization required. Browserless tem 0 unidades. Não burlar essas barreiras com CDP pelo shell.

## Objetivo
Preparar publicador de vídeo via API Buffer, exigir a identidade LinkedIn Page 145345334, manter metadados Anthares e diferenciar agendamento Buffer da efetiva publicação LinkedIn. Nenhuma publicação de prova sem conta conectada e chave de API no gerenciador de segredos. Preservar fila Neon e rate limits reais.

## FAILED_AVOIDED
Não capturar cookies ou tokens do perfil, não automatizar sessão recusada, não inventar Buffer channelId, não repassar segredos em GitHub, não confirmar ledger só com post agendado.

## SUCCESS_SIGNAL
Adapter fail-closed, autenticação explícita, canais verificados, testes sintéticos e CI isolado. Ativação de produção depende de LinkedIn canal real, API Key segura, identidade validada, integração com ledger e publicação externa confirmada.

## FAILURE_SIGNAL
Sem canal, sem chave, mismatch de página, GraphQL error ou resposta ambígua: não marcar publicada, não repetir post cegamente.

## TEST_VALIDITY
Somente testes determinísticos, sem posts reais; evidências e pendências separadas.
