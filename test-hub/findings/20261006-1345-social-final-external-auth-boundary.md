# Social final closure — external authorization boundary
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: social-auth-browser-final
COMMIT: c35b512cff9df56e227eb1301c0dc8f7cb1d86af
SUPERSEDES: none

## Baseline
Direct Instagram/Threads/X adapter contract remains PROVEN by run 37470378653. X paid API remains disabled by default.

## Probes executados
- Chrome está ativo no PC e há múltiplos perfis locais.
- Nenhum Chrome DevTools endpoint existente em 9222-9225; portanto não há sessão já controlável sem reiniciar/abrir uma instância dedicada.
- Probe de histórico não produziu evidência válida de sessão Meta/X reutilizável.
- Perfis Chrome possuem account_info, mas isso comprova apenas identidade Chrome/Google, não autenticação Meta/X.
- Busca ampla por arquivos de credenciais foi INVALID por timeout e não conta como ausência de credenciais.

## Resultado
Não existe evidência suficiente para promover Instagram/Threads/X a real-post PROVEN. Instagram/Threads permanecem AUTH_REQUIRED no ponto de consentimento OAuth Meta. X permanece BLOCKED_PAID_API na API oficial; rota browser exige uma sessão autenticada/controlável.

## Consequência operacional
Toda infraestrutura anterior deve ser preservada. Próxima ação humana mínima e inevitável: autenticar/consentir Meta e X em uma sessão controlável. Depois disso o agente pode executar canários e registrar remote_id + confirmation_evidence. Não armazenar cookies/senhas/tokens no Hub.

## Lease
Lease social-auth-browser-final encerrado: não há mutação legítima adicional capaz de fabricar consentimento de terceiros.
