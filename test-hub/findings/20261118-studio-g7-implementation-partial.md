# Anthares Studio G7 — entrega de domínios privados (parcial)
STATUS: PARTIAL
AREA: anthares-studio/g7/production
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g7-domain-workspaces-20261118
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/321
COMMIT: 25a7ad02dd9a45f3c6e5345140381a76faddc400
SUPERSEDES: test-hub/findings/20261118-studio-g7-domain-lease.md
LEASE: terminated, agent-owned temporary git and Chrome resources cleaned.

## Entrega comprovada
- Novo CPT privado e API G7 com registros versionados de pesquisa, planejamento, elementos complementares, causalidade, continuidade, exercícios, curso e revisão; autor/projeto e revisões obrigatórios.
- Workspace autenticado nas abas do projeto; gráfico, cronologia, relações ACF, modelos estruturais, desafio 20 contos + 20 crônicas, contextualização Hotmart, busca e exportação.
- Arquivo privado até 3 MB com MIME permitido e acesso proprietário, fora do public_html. Somente rotas de leitura/permissão homologadas.
- Validações PHP lint + qa/manifest-coverage-preflight.py --check: 679 auditable, 679 assigned, exactly once. JavaScript parse PASS.
- Em WP REST: G7 GET owner 200, outra conta 404, visitante 401; /g7/progress mesmo resultado. Arquivos id inexistente owner 404 e visitante 401. Browser autenticado confirmou painéis, ACF ready e formulário de modelo Save the Cat com 15 beats.
- Autorização ACF passou a READY na produção por mudança existente; este job preservou sinalizadores e dados originais.

## Pendências e limites
- Sem teste efetivo de escrita/criação/exclusão em registros G7 e upload: ferramenta já bloqueou escrita autenticada em conteúdo; respeitar recusa e não repetir com WP-CLI para executar a mesma mutação.
- Modelos G7 de apoio em CPTs privados complementares; migração ACF e contratos comerciais permanecem dependências separadas.
- O catálogo de 188 itens ainda NÃO está 100% coberto; faltam integração real de publicação pública, direitos de acesso pagos, Runas, leitores beta externos, colaboração e métricas de retenção com consentimento.
- Publicação/payments/Runas não foram ativadas, nenhum projeto privado divulgado, nenhum backup extra criado, nenhum pagamento iniciado.
