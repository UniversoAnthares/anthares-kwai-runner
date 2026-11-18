# Studio G6 — menu global com cinco destinos
STATUS: RUNNING
AREA: anthares-studio/g6/navigation
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g6-sidebar-five-items-20261118
POLICY_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
REPO: UniversoAnthares/anthares-wordpress
BASE: fix/studio-pilot-fallback-safety-20261117 HEAD ac0e9b1e384a06fc1a861802fdc1c647e7cdead7
SCOPE: exclusivamente anthares-studio/assets/estudio.js; retirar a sexta entrada global Lixeira, já disponível em Meus projetos. Preservar o handler e a rota #studio/lixeira; preservar cinco destinos globais e sete abas.
SOURCE_VERIFIED: Hostinger live 18/11/2026: módulo original intocado; 13 testes Python PASS, PHP 8.3 lint PASS; interface headless isolada com mock mostra seis destinos no clone.
NO_CONFLICT: branch própria e patch mínimo. Não alterar legado, dados, pagamentos, permissões, backups e publicadores.
QA_PLAN: testes estáticos, Node --check, inspeção DOM isolada, regressão de rota Lixeira, comparação de hashes do legado.
ROLLBACK: restaurar a cópia SHA256 do JS anterior se houver implantação autorizada; nenhum registro pode ser tocado.
