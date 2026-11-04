# AOI #7 — lease de diagnóstico da saúde Forgejo e do espelho
STATUS: RUNNING
AREA: architecture/forgejo-health-and-mirror-receipts
DATE_UTC: 2026-11-04T21:22:01.728Z
EXPIRES_UTC: 2026-11-04T21:52:01.728Z
OWNER: chatgpt-aoi7-20261104
BASE_HEAD: 24eb46eca952ae10c4883727f1e594403d98c2b8
ITEMS: [7]
SCOPE: finding técnico somente, nenhuma operação no Hostinger ou GitLab, nenhum workflow, nenhuma publicação.
BASELINE_PROVEN: API pública Forgejo HTTP 502; recibo GitHub→Hostinger anteriormente HTTP 200 com SHA antigo, agora HTTP 503 por integridade/recência; PHP proxy usa Unix socket.
FAILED_AVOIDED: não contornar recusa administrativa Forgejo, 403 GitLab, indisponibilidade de sessão SSH, permissão ausente da extensão Hostinger, custos, credenciais e runner Windows; não mudar hosts, cron, CDN nem branches.
SUCCESS_SIGNAL: readback público documentado, risco de espelho obsoleto classificado e critério de restabelecimento definido.
FAILURE_SIGNAL: alegação falsa de recuperação ou nova escrita remota sem autorização.
TEST_VALIDITY: apenas consultas públicas e leitura de fonte; nenhuma execução real do daemon/cron.
