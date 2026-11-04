# AOI #7 — Forgejo origin HTTP 502 e recibo de espelho HTTP 503
STATUS: PARTIAL
AREA: architecture/forgejo-health-and-mirror-receipts
ITEMS: [7]
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T21:22:51.162Z
SUPERSEDES: lease-20261104-aoi7-forgejo-health.md
LEASE: CLOSED
LEASE_OWNER: chatgpt-aoi7-20261104
SOURCE_HEAD_AT_START: 24eb46eca952ae10c4883727f1e594403d98c2b8
COST_ADDED: 0
PRODUCTION_CHANGE: NONE

## Evidência live
- `GET https://anthares.us/forgejo/api/v1/version` IPv4: HTTP 502, body literal `Forgejo origin unavailable`.
- `GET https://anthares.us/forgejo/` IPv4: HTTP 502.
- `POST https://anthares.us/forgejo-sync.php`: inicialmente HTTP 200, `SYNC_PROVEN bde5364b90efc68925be560c429a8704257c691e` (espelho de checkpoint antigo); depois, HTTP 503 em duas leituras separadas. O PHP `infra/forgejo-proxy/sync.php` responde 503 por recibo ausente ou com mais de 2400 segundos, failures não vazios, estado inválido ou SHA do bare diferente do recibo. O motivo específico entre estas condições ainda está sem prova.
- A fonte GitHub `main` já possuía commit `24eb46eca952ae10c4883727f1e594403d98c2b8`, portanto o último espelho observado estava atrás. **RPO atual não comprovado.** Não promover o espelho para failover.
- Fonte `infra/forgejo-proxy/index.php` usa cURL sobre `/home/u566597497/.anthares-forgejo/forgejo.sock` e emite exatamente `Forgejo origin unavailable` se a chamada falha. A causa provável é indisponibilidade do daemon/socket. Há precedente verificado em `test-hub/findings/20261006-1058-forgejo-recovered-gitlab-oauth-gate.md` (daemon parado/socket obsoleto); o estado atual do processo em Hostinger não foi observado.
- Conexão ARA ContextRouter Hostinger `listener-status` respondeu OK, mas esse contrato só oferece `identity` e `listener-status`, sem execução de cron ou leitura de arquivo de status. Uma tentativa somente-leitura de SSH no contexto SYSTEM não encontrou a chave do perfil Lucas e retornou autenticação recusada; não houve troca de identidade, chave, permissão nem segundo SSH.
- A aba Hostinger está visível no navegador, porém a extensão conectada recusou acesso à página por falta de permissão do host. Não foram feitos controles administrativos alternativos que contornassem os bloqueios anteriores de segurança Forgejo.

## Correção operacional exigida, sem aumento de custo
1. No canal administrativo Hostinger oficialmente autorizado: verificar o cron existente `0,30 * * * * bash /home/u566597497/.anthares-forgejo/git-mirror-hostinger-scheduled.sh`, o último exit/log, o estado do `git-mirror-hostinger-status.json`, a integridade do bare e a disponibilidade do processo Forgejo e seu socket. Evitar criar cron duplicado ou reiniciar processos com outra lease ativa.
2. Corrigir a causa observada, aguardar recibo recente; verificar `POST /forgejo-sync.php = 200` e SHA igual ao HEAD canônico após o cron; exigir GET `/forgejo/api/v1/version = 200`.
3. Verificar os 15 repositórios/refs, incluindo 2 origens vazias, e registrar execuções recentes contínuas antes de marcar #7 DONE; #4 exige comprovação separada de CI no repositório principal.
4. Preservar as recusas anteriores de acesso administrativo/autenticação Forgejo e históricos GitLab; não recorrer a canal alternativo para contorná-las. Respeitar cancelamento por quota, sem planos pagos.

## Resultado
O ramo de espelhamento previamente comprovado tornou-se inapropriado para failover atual; #7 permanece PARCIAL. Nenhuma operação Git no Hostinger, workflow, serviço, conta, segredo, publicação, Neon ou runner foi alterada nesta auditoria. O registro evita usar um SHA antigo enquanto o endpoint está indisponível.
