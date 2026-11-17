# G7 — interface de fichas narrativas e curvas, QA isolada
DATE: 2026-11-17
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
SOURCE: UniversoAnthares/anthares-wordpress
BRANCH: feat/studio-g7-curves-ui-admin-guard-20261117
BASE: ad20db193775c1693fa41819da69ac82f32663f1
PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/318 (DRAFT)
LEASE: test-hub/findings/20261117-studio-g7-curves-ui-admin-guard-lease.md

## Entrega de código
- G7 `anst_story_ready(true)` exige o gate compartilhado G4 quando disponível. No ramo anterior ao merge, fallback seguro bloqueia escrita de não administradores. Ativação ACF continua sujeita à aprovação dupla e ao contrato G5.
- `assets/estudio.js`: aba Análises apresenta SVG com quatro curvas reais (duas tensões, conflito, fortuna) obtidas de `/story/curves`; escala e fonte legíveis, dados ausentes interrompem a curva, sem valores estimados; tabela preserva ordem do leitor e tempo da história.
- Planejamento > Elementos inclui painel separado de fichas G7 e relações privadas: personagens, lugares, grupos, eventos, cenas, beats, conflitos, fontes, edição de atributos ACF, paginação e exclusão de vínculo. Pastas legadas continuam preservadas.
- `class-anst-story-domain.php`: permite apagar valor numérico opcional sem inserir zero, mantendo validações de intervalo.

## QA
- Execução isolada de HEAD `bb424905e6f852da2943b308a54835dbea2909b5`: 60/60 unittest PASS; PHP lint 2/2 PASS; QA manifest 676/676; 11 verificações do orquestrador PASS.
- Execução isolada de HEAD `5bf25f4f873ef0d04fe2c20448aa04c285ec73bb`: 62/62 unittest PASS; PHP lint 2/2 PASS; QA manifest 676/676.
- Simulações do JS com API em memória: 11/11 pontos SVG/ordenacao, 9/9 painel de fichas/links/escape, 4/4 formulários criar/editar/relação/falha de rede. Não constituem smoke REST real.
- Os checkouts foram criados em diretórios privados efêmeros na Hostinger e removidos automaticamente em `trap` após os testes; apenas operações remotas invisíveis (Session 0), sem arquivos no PC.

## Restrições mantidas
- ACF em produção permanece OFF. G7 não foi implantado no WordPress e a PR #318 continua DRAFT sobre a branch G7 isolada.
- Testes reais com mutação REST e acesso à aba autenticada permanecem bloqueados pelas verificações de segurança já registradas no G4; nenhuma rota alternativa foi utilizada.
- Requisitos B05–B30 permanecem abertos onde não há prova de implementação integral; comercial/publicação exige contratos e consentimentos específicos.
