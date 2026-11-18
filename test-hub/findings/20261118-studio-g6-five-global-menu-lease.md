# Studio G6 — regressão de sexta entrada global e correção isolada
STATUS: RUNNING
AREA: anthares-studio/navigation
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g6-five-global-menu-20261118
SOURCE: UniversoAnthares/anthares-wordpress PR #321, ref fix/studio-pilot-fallback-safety-20261117, HEAD ac0e9b1e384a06fc1a861802fdc1c647e7cdead7
BASELINE: Studio publicado JS SHA256 ffcb43e7b33160d16af8a4c5dd8d4abd845c657dc42c58fac7caf0faac0ecc4d. Backend isolado do legado, sem alteração de bancos.
PEER: GitLab branch da PR #321 indisponível (404), não espelhar às cegas.
SCOPE: corrigir somente o menu global do frontend no Studio; remover o item Lixeira do menu lateral e manter acesso contextual em Meus projetos. Teste automatizado de cinco entradas no frontend usando dados sintéticos, sem autenticação ou operações reais.
EVIDENCE: inspeção do sidebar() em PR #321 e na Hostinger mostra seis entradas; Browserless headless em origem neutra, com fetch REST integralmente simulado, confirmou seis entradas nas telas Início, Meus projetos, Banco de ideias, Ajuda e projeto, e os sete grupos internos. O contrato de 13/11/2026 exige exatamente cinco globais: Início, Meus projetos, Banco de ideias, Curso de Escrita, Ajuda.
DEPENDENCIES: PRs #312, #316, #320, #321 seguem em revisão e não serão alteradas; tratar esta correção como PR dependente, sem merge ou deploy automático.
SAFETY: não tocar /estudio, dados AEST/ANST, flags de escrita ou ACF, credenciais, sessões de navegador, plugins em produção. Manter os testes de isolamento e QA. Após patch: provar cinco globais e sete grupos em teste sintético; homologação em conta autenticada permanece separada.
ROLLBACK: descartar a branch isolada; nenhuma operação em produção está autorizada por esta coordenação.
