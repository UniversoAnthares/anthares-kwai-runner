# Anthares Studio — correções de paridade e regressão (execução isolada)

STATUS: RUNNING
AREA: anthares-studio/parity/qa
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-parity-20261118
SOURCE: UniversoAnthares/anthares-wordpress PR #321 HEAD ac0e9b1e384a06fc1a861802fdc1c647e7cdead7
BRANCH: fix/studio-parity-contract-20261118
PEER: GitLab não promovido; nenhum espelhamento automático autorizado.
SCOPE: somente correção do menu lateral 5 itens do Studio e adaptação de testes regressivos aos recursos novos já existentes; manter Lixeira acessível em Meus projetos. Preservar todas as funcionalidades originais, o plugin /estudio, dados e permissões.
BASELINE: checkout efêmero em Hostinger do SHA ac0e9b1: 90 testes Python, 3 falhas (Lixeira global extra; conjunto de ações com quatro recursos extras válidos; teste de hash integral CSS que inclui acréscimos novos); PHP 8.3 lint PASS; manifest coverage 676/676 PASS. Checkout da auditoria removido e ausência confirmada.
SUCCESS_SIGNAL: todos os testes Python aprovados; sintaxe PHP; integridade de escopo CSS; JS syntax; QA manifesto; nenhum dado ou código do legado alterado.
CONCURRENCY: branch nova, isolada da PR #321 e da integração #320; testar antes de eventual promoção. Proibido forçar merge, substituir arquivos de produção sem ler estado atual ou permitir gravação sem permissão.
ROLLBACK: descartar a branch e PR draft; nenhuma mudança em produção até QA e reconciliação de hashes.
