# TikTok LIVE - inventario de Android persistente fora dos dispositivos
STATUS: PARTIAL
AREA: tiktok-live-persistent-android-host
DATE: 2026-11-10
LEASE_STATUS: CLOSED

Railway: dois projetos conectados, accurate-commitment e worthy-heart. Em cada um existe anthares-telegram-relay. Nenhum Android persistente identificado. Nao alterar relays.
MeshCentral: dois registros DESKTOP-FTDK0HP, mesma maquina pessoal Windows 10; inelegivel para operacao sem PC.
Hostinger SSH: Linux x86_64, conta nao root, /dev/kvm ausente e inacessivel. Teste somente leitura feito por canal ja autorizado. Inelegivel para Android acelerado.
Segredos VPS_HOST, VPS_USER e VPS_PASSWORD configurados no Github. Runs 42942858375 e 42942963464 tentaram SSH em portas comuns, inclusive 65002, e emitiram TIKTOK_VPS_SSH=UNREACHABLE. VPS ainda nao caracterizado.
GitHub Ubuntu Actions: KVM e Android 35 comprovados, mas runner termina e descarta aparelho; Cloudflare Quick Tunnel expira. Identidade Google nao preservada.
Existe historico de snapshot Android reutilizado entre jobs em test-hub/findings/20261009-kwai-speed-skip-cold-boot-benchmark.md, mas prova de identidade Google entre execucoes e criptografia ainda pendentes.

DECISAO: nenhum host conectado comprovou KVM, armazenamento duravel, 24h continuo e custo zero. Nao contratar servico e nao afirmar TikTok LIVE ativa. Proxima alternativa: estudar snapshot AVD criptografado e restauro em runner GitHub com prova do login em uma segunda execucao; isso nao representa servidor ligado 24h.
Evidence: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42942858375 and https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42942963464