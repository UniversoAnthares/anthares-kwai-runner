# Leituras beta disponíveis — seção Home publicada
STATUS: PROVEN
AREA: wordpress-home-beta-opportunities
DATE: 2026-10-31
RUN: Hostinger SSH + WP-CLI read-only
JOB: chatgpt-20261031-home-beta-opportunities
COMMIT: 5f41ccd458521f8387947c49fd96d1044933f29c
SUPERSEDES: test-hub/findings/20261031-lease-home-beta-opportunities-gpt6.md

## Resultado
PR #214 de `UniversoAnthares/anthares-wordpress` mesclada. Nova seção `leituras-beta-disponiveis` com cards contendo autor, título, vagas livres, preço em Runas e ação de leitura beta. Seção publicada no layout do Laboratório em bloco 3 (área de participação) para os cinco perfis, exclusivamente papel `anthares`. Regra especial também libera ao papel `anthares` o fluxo de aceitar leituras, mantendo os requisitos dos outros papéis.

## Provas
- QA externo Hostinger: PHP 8.3 lint em 5 arquivos PASS, manifest coverage PASS 601/601 exactly once, QA orchestrator PASS.
- Divergência prévia do menu lateral da Home foi reconciliada no código com manutenção de 'Menu' recolhido e 'Início' expandido.
- Hostinger: 6 arquivos publicados com backup privado, comparação posterior 6/6 `MATCH` byte a byte com GitHub main.
- WP-CLI: `REGISTERED=yes`, `ROLE=yes`, `PROFILE_1=yes` até `PROFILE_5=yes`.
- WP-CLI: `RENDERED=yes`, `ANON_DENIED=yes`, `RUNAS_UNCHANGED=yes` (contagem de registros mantida).
- Ofertas ativas na consulta real: `ACTIVE_OFFERS=0`; estado editorial exibido: 'Nenhuma leitura beta disponível no momento.'; consultas SQL sem erro. Nenhum conto ou transação foi criado no teste.
- Clone/temp no servidor externo removido após execução. Nenhum trabalho salvo no PC.

## Limites
A seção foi efetivamente implantada, mas não havia ofertas para validar card preenchido por oferta real. Os testes funcionais de aceitar um conto real e transferência de Runas não foram executados (evitar efeitos comerciais não solicitados). Critérios de autoria, status de conto, ocupação e reservas são verificados em SELECT read-only no template. Para futuras ofertas, usar dados reais de autor e fluxo existente.
Lease encerrado.