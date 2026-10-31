# Microseção de leitura beta em três posições com carrossel
STATUS: PROVEN
AREA: wordpress-home-beta-opportunities
DATE: 2026-10-31
RUN: Hostinger SSH / WP-CLI
JOB: chatgpt-20261031-beta-three-slots
COMMIT: d7ca261da039e53310317cf6719341709b4f6fa7
SUPERSEDES: test-hub/findings/20261031-lease-home-beta-carousel-gpt6.md

## Resultado
- WordPress PR #217 mesclada (squash `d7ca261da039e53310317cf6719341709b4f6fa7`).
- Seção `leituras-beta-disponiveis` desenhada como primeiro de três slots internos na faixa total do Laboratório. Um item de cada vez, autor/título à esquerda; vagas e Runas em destaque à direita; botão de próxima oferta em ciclo quando >1.
- Role exata `anthares`: lista ofertas ativas e inteiramente financiadas inclusive do próprio perfil; outros papéis continuam bloqueados pelo template e elegibilidade. Não há card pessoal separado, gerenciamento nem aviso legado. Clique no título abre fluxo existente de leitura do conto. Dono `anthares` recebe pré-visualização de texto readonly no fluxo existente, sem formulário nem pagamento por autoavaliação.
- As posições internas 2 e 3 ficam reservadas, sem seções adicionais inventadas.

## Prova
- QA externa Hostinger PHP 8.3 lint PASS dos 3 arquivos PHP; manifesto 601/601 exactly_once PASS; orquestrador QA PASS.
- Antes de implantar, quatro arquivos de produção comparados byte a byte ao commit pai do main GitHub, `LIVE_MATCH_OLD` para todos. Implantação com backup privado, `DEPLOY_PASS=4/4`, `MAIN_COMMIT=d7ca261da039e53310317cf6719341709b4f6fa7`.
- Depois: `MATCH` em cada um dos 4 arquivos; CSS público HTTP 200.
- WP-CLI: `OFFERS_ALL=1`, oferta ativa 3 vagas, 11 Runas, financiada, status beta válido, `ELIGIBLE_OFFERS=1`; `RENDER_SLOTS=2`, `RENDER_SLIDES=1`, `OWN_MANAGE_HIDDEN=yes`, `LEGACY_NOTICE_HIDDEN=yes`, `NEXT_ARROW=no` (correto: uma oferta).
- WP-CLI no próprio conto: `SELF_NO_PAYMENT_FORM=PASS`, `SELF_CONTENT_PRESENT=PASS`. Comparação textual `SELF_READONLY` falhou em frase com acento na verificação, enquanto o próprio conteúdo e a ausência do formulário foram confirmados. Navegação da seta para >1 oferta ainda não homologada em navegador por haver apenas uma oferta real no banco.
- Não houve novas ofertas, saldos alterados, pagamentos ou operações no PC. Encerrar leases da área.