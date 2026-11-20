# Anthares Studio — homologação interativa com sessão autenticada (2026-11-20 UTC)

## Origem e isolamento
- Chrome dedicado com pasta local `D:\AntharsWork\browser-profiles\AntharesStudioAuth`, porta CDP loopback 9241, sessão Windows interativa; página real `https://anthares.us/studio/`.
- Autenticação comprovada por barra WordPress, `aest-access-gate=false`, `window.AntharesEstudio.initial` presente e 22 projetos carregados.
- Aba técnica criada para QA `EDD663B424BD9F022674C118AA9E42B7`; fechada após verificação via `Target.closeTarget` success=true. Aba pessoal original mantida.
- Testes isolados em projeto próprio `21998`, título único `QA-HOMOLOGACAO-UI-20261120`; capítulos `21999`, `22000`; nota `22001`. A criação de nota retornou uma falha de comunicação do remoto depois do efeito; reconciliação WP-CLI confirmou exatamente uma nota criada (além de uma fixture preexistente distinta, intacta).
- Depois de revisar IDs/tipos/títulos/autoria, exclusão definitiva somente desses quatro IDs; `wp post get` para todos retornou `Could not find the post`. `wp post list --post_type=anst_projeto --post_status=publish --author=1 --format=count` = 22, mesma linha de base. Dados de usuários preservados.

## Evidências de êxito
1. Cinco opções de entrada em Novo projeto presentes; ação `start` criou projeto privado ID 21998 e abriu a estrutura correta.
2. Formulário de renomeação exibido, submit gravou o título, render e POST confirmados.
3. Navegação de topo: Início, Meus projetos, Banco de ideias, Ajuda e Novo projeto; controles `data-action=nav` disponíveis. Houve demora de re-renderização (aprox. segundos) ao navegar, mas rotas mudaram corretamente quando aguardadas.
4. Nove áreas internas no projeto temporário abriram em suas URLs: visao, pesquisa, planejamento, elementos, estrutura, manuscrito, analises, revisao, publicacao; headings coerentes, sem transbordamento na largura testada.
5. Manuscrito: botão `new-chapter` criou capítulo 21999, Quill 2 carregou, setText(source=user) inseriu texto de teste, botão salvar acionado, GET bootstrap de escopo confirmou Delta persistido e resposta HTTP 200; status `Salvo automaticamente`.
6. Segundo capítulo 22000 criado via UI; reordenação por botão `chapter-move` colocou 22000 antes de 21999; ordem confirmada em GET bootstrap e DOM.
7. Pesquisa: form `data-form=note` enviado com texto marcado, criação da nota 22001 confirmada via WP-CLI e título.
8. Layout de lista de capítulos: 360, 390, 768 e 1440 px simulados via DevTools, overflow=false nas quatro larguras; emulação removida ao final.
9. Tema: botão alternou preferência de modo visual, clique duplo restaurou aparência escura; como o valor prévio de armazenamento era null, chave localStorage removida ao final para restaurar o estado anterior. 
10. Testes servidor do passo anterior: 51/51 Python, 14/14 JS parse, PHP lint, 54 afirmações REST (criação, salvamento, lixeira/restauração, hashes/revisões, permissões). Não foram repetidas escritas da suíte transacional nesta execução.

## Lacunas que impedem declaração de E2E total
- Botões especializados de cada subtela (mural visual, fichas, versão/restauração pela interface, editor Quill avançado, importação/exportação de arquivos, comentários, enquetes, leitores beta, Mentores, publicação) não receberam testes de clique individual nesta rodada.
- O teste de acessibilidade visual completo com screenshots e gestos reais em todas as telas, dois usuários de permissões distintas e validação do fluxo comercial externo permanece pendente.
- A alternância de arquivamento por UI teve resultado de retorno à condição inicial, mas uma resposta remota falhou durante a sequência. Tratar como inconclusiva; o backend já havia passado no teste REST de arquivamento.
- O nome de perfil `AntharesStudioAuth` é um diretório técnico isolado do Chrome, não uma opção exibida no seletor normal de perfis; sessão foi comprovadamente autenticada.

## Resultado
Parcial com forte cobertura das operações principais. Nenhum defeito reproduzível nos percursos ensaiados, sem alterações residuais no conteúdo. Manter explicitamente pendências de QA integral; não afirmar cobertura de cada botão.
