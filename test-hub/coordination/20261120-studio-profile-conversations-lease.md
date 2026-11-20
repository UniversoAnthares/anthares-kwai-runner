# Lease — Anthares Studio, pendência urgente 6: conversas no perfil
OWNER: ChatGPT / STUDIO_PROFILE_CONVERSATIONS_20261120
STATUS: CLOSED_SUCCESS
SCOPE: anthares-studio/includes/domain/class-anst-g7-profile-conversations.php, anthares-studio/anthares-estudio.php, anthares-customify/author.php, qa/anthares-qa-sections.json e anthares-pix-sales/qa-sections.json. Separar comentários de perfis dos comentários de capítulos.
CONSTRAINTS: preservar /estudio/ e dados reais; GitHub PR + conferência de produção; scripts ocultos; sem escrita em perfis alheios, sem envio de mensagens reais em testes; moderacao, privacidade, nonce, anti-spam, testes e reversão.
START: 2026-11-20
EXIT: atualizar resultado e fechar o lease; nenhuma alteração em arquivos de outros fluxos.

END: 2026-11-20
RESULT: Item 6 (conversas no perfil publico) implementado e homologado no Anthares Studio.
GITHUB: PR UniversoAnthares/anthares-wordpress#392 merged; main commit d688bded6e81fa3f3c9fac330feda172327db6a6.
PRODUCTION: Hostinger Studio root SHA b8079f7971bd64a1257208ce70f1c5c46af5d4f1; profile wall SHA 0badfa452e73c2a0c616c5afde22fe118cee80c3; active author theme preserved SHA 7edba6281348a6cfa62807e19c3b1c31d679f87b.
QA: PHP 8.3 lint PASS; 15 structural checks; 14 transactional comments/profile/reply checks PASS; 2 transactional notifications checks PASS; both transactions ROLLBACK; 0 residual profile-wall posts; 0 QA temporary PHP files. /studio/ and /estudio/ HTTP 200; live author page contains profile mount script.
BACKUP: original production Studio root backed up privately, outside public_html, SHA f8c81ec5e27f2412907f4fbe62ce814114554eae.
FINDING: test-hub/findings/20261120-studio-profile-conversations-item6.md.
