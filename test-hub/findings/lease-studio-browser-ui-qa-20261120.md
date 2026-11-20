# Lease de homologação interativa do Anthares Studio — 2026-11-20
OWNER: ChatGPT / ANTHARES_STUDIO_BROWSER_UI_QA
STATUS: CLOSED_PARTIAL_FULL_UI_QA_PENDING
START_UTC: 2026-11-20T01:08:00Z
EXPIRES_UTC: 2026-11-20T01:38:00Z
SCOPE: teste UI na sessão Chrome AntharesStudioAuth (127.0.0.1:9241), usando uma aba própria EDD663B424BD9F022674C118AA9E42B7, sob autenticação comprovada.
BASELINE: 22 projetos reais já existentes na conta; script/REST testes anteriores 51/51 e 54 asserts em transação, todos PASS. Nenhuma alteração em projetos anteriores.
ALLOWED: criar 1 projeto com título exclusivo QA-HOMOLOGACAO-UI-20261120; testar notas, capítulo, mural, editor, navegação, análises, modo claro/escuro, rotas, mobile; excluir apenas os IDs realmente criados após rever autoria e título. Guardar confirmação de limpeza.
FORBIDDEN: tocar nos projetos reais, fazer publicação pública, pagamentos, contatos externos, alterar acessos/entitlements. Não extrair cookies, credenciais ou texto pessoal.
EXIT: fechar somente a aba própria, preservar janela Chrome dedicada para login persistente, encerrar lease e registrar resultados.

CLOSED_UTC: 2026-11-20T01:32:00Z
RESULT: Autenticação real comprovada; 9 áreas internas, editor Quill com save, capítulos com ordem, anotação, tema, breakpoints 360/390/768/1440. Projeto 21998 e filhos 21999/22000/22001 excluídos definitivamente e confirmados inexistentes; contagem voltou a 22 projetos. Aba própria fechada; navegador autenticado do usuário preservado. Pendente inventário de botões especializados e teste de importações/exportações. Relatório: test-hub/findings/20261120-studio-browser-ui-qa-report.md
