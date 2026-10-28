# Item 9 — restaurar atestado de mídia Threads 7747–7788
STATUS: RUNNING
AREA: threads/cloud-media-exact-lookup
DATE: 2026-10-28
OWNER: ChatGPT item 9
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40785907390
JOB: 123158917480
COMMIT: 9f31a8c865adaa608b2815a40245f800f729ae84
SUPERSEDES: none
LEASE: escopo exclusivo config/threads-verified-transcripts.json; expiração máxima 30 minutos após abertura, sujeito a HEAD/fencing e a leases concorrentes.

BASELINE_PROVEN: PR #1732 (merge 62c6a653) incluiu atestado original de transcrição do MP4 e SHA-256 para o corte g1:fOmihuHUT1M:7747:7788, mas PR #1736 (a90fe0aa) removeu exatamente suas 75 linhas numa alteração sobre Codeberg. Registry GitHub e GitLab atuais têm 164 chaves e omitem a identidade. Run #40785907390 falhou antes de publicar com WORDPRESS_403_EXACT_ATTESTATION_REQUIRED neste corte. Neon conserva fila/fencing, sem permissão para retry incerto.
FAILED_AVOIDED: não alterar WordPress, autenticação, gates, quota, dados de fila, clipe, SHA, publicador ou outras 164 entradas. Restaurar somente a evidência já atestada do próprio commit #1732.
SUCCESS_SIGNAL: JSON válido; 165 entradas; atestado exato id/attachment_id/source/interval/SHA/verified conforme commit original; arquivos pré-existentes imutáveis; testes estáticos editoriais/lookup aprovados; prova de mídia SHA permanece exigida pelo publicador antes de reivindicar lease.
FAILURE_SIGNAL: divergência de fonte/identidade/SHA, head concorrente, lease concorrente, falha de JSON ou validação, ou publicação incerta não reconciliada; abortar alteração ou deixar em revisão.
TEST_VALIDITY: nenhum post experimental; GitHub PR com validação somente de código; publicação exclusivamente pelo primário cercado por Neon, sob rotina e limites vigentes. Evidência de finalização exige confirmação remota individual.
