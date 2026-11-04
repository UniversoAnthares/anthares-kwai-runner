# Cloudflare Workers quota — ARA verificado em Vercel/Neon; atribuição pendente
STATUS: PARTIAL
AREA: cloudflare-worker-request-quota / remote-admin / cortes
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T13:08:13.683Z
RUN: none
JOB: none
COMMIT: 5440ecb4063b4d784311cb97aad41b4b329a906d
SUPERSEDES: 20261104-lease-cloudflare-ara-backend-attribution.md
LEASE_AREA: cloudflare-per-worker-causal-audit
LEASE: CLOSED
GOVERNANCE_MANIFEST: 223433740e807a90

## Provas diretas
- Aviso Cloudflare entregue ao titular: Workers/Pages Functions em conta Free atingiu 100000 requests diários em 2026-11-03; reset 2026-11-04T00:00:00Z. Prova do limite da conta, sem análise por script.
- Anthares Remote Cloudflare MCP / session_status: `connected=true`, `backend=vercel-neon`, heartbeat às 2026-11-04T13:03:33Z, versão 0.3.1; uma única instância C8 ativa em leitura de processos, PID 9664. Há tarefas supervisórias registradas, mas nenhum segundo agente listado.
- PR #2084 incorporada na main: corrige polling ocioso 2s -> 15s em hosts HTTPS *.workers.dev e falhas 3s -> 60s. O agente vivo citado usa Vercel/Neon: economia Cloudflare para essa instância ainda não foi demonstrada, e a implantação do binário também está pendente.
- Neon SELECT agregado do alvo kwai:lucasrosalem: 456 confirmed e 68 uncertain; preservar o bloqueio contra reenvio.

## Diagnóstico e aceite
O maior consumidor da cota de Workers e Pages permanece UNVERIFIED. NÃO atribuir o alerta a um agente específico com base apenas em loops de código. Para encerrar, consultar Cloudflare Workers & Pages Analytics de 2026-11-03 por script e hora, corrigir o(s) clientes reais que mais acionaram o Worker e comparar o uso após mudança com logs e custo zero. Nada foi alterado em produção nesta auditoria; não adicionar cobrança, não desarmar controle de segurança, não publicar vídeos por teste. Sem novas sessões de browser ou arquivos no PC.
