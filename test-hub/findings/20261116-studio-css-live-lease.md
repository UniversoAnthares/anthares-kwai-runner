# Execução isolada — Deploy CSS /studio via SSH protegido (2026-11-16)
STATUS: RUNNING
AREA: anthares-studio-layout-css-only
DATE: 2026-11-16
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-css-live-20261116
BASELINE_PROVEN: PR anthares-wordpress#313 head 1f6d1c87392805224342dce0fdef6f32a5c27284; live stylesheet ainda possui 509 page-id-19344 e 6 post-19344. Novo plugin em /studio, PHP G4 em produção; plugin original intocado.
FAILED_AVOIDED: SSH via conta Windows SYSTEM rejeita chave do usuário. A rota de CI utiliza ponte SSH Hostinger já existente e protegida, declarada no workflow kwai-live-6h.yml, sem ler, registrar ou divulgar segredo. Recusa da credencial interrompe o deploy.
SUCCESS_SIGNAL: arquivos CSS de produção sem page-id-19344/post-19344, com anst-studio-page e escopo correto; PHP com body_class exclusiva; cópia reversível privada fora do public_html; original sem mudanças; flags de escrita OFF.
FAILURE_SIGNAL: chave restrita, GitHub quota, SHA de origem inesperado, hostkey inesperada, testes falham, publicação parcial ou cache CDN antigo.
TEST_VALIDITY: comparação real SHA/bytes antes/depois no servidor; validação PHP 8.3 -l e resposta HTTP de CSS com URL de cache-busting; sem afirmar comparação visual autenticada sem captura.
SCOPE: apenas anthares-studio/anthares-estudio.php, assets/estudio.css, assets/estudio-dark.css.
ROLLBACK: backups byte-identical em armazenamento privado Hostinger, restaurar atomicamente os três arquivos se falhar.
BLOCK: nao alterar anthares-estudio, outros plugins, options, banco, fila, serviço, cron ou publicadores; nao habilitar gravação nem reiniciar máquinas.
SUPERSEDES: test-hub/findings/20261116-studio-css-page-scope-lease.md
