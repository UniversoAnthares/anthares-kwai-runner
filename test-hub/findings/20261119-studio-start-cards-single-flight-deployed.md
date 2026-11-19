# Anthares Studio — cartões de criação com bloqueio de concorrência

STATUS: PARTIAL
AREA: studio/g4/project-creation
DATE: 2026-11-19
RUN: Anthares Remote e Hostinger SSH; job e1565f48739a8d5bf065bb17924125c4
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/338
COMMIT: 4267148e6c56162f4430ae506ccd85de3c2fb3c1
SUPERSEDES: none

## Defeito observado
O titular relatou que os quatro cartões da tela /studio/#studio/novo pareciam não reagir aos cliques. Consulta de metadados no WP-CLI de produção identificou cinco projetos anst_projeto criados entre 2026-11-19 11:10:21 e 11:10:34 (relógio WordPress), autor 1. IDs 21803, 21804, 21805, 21806, 21807. Todas as criações foram preservadas; nenhum projeto ou manuscrito foi excluído.

## Alteração implantada
No JavaScript ativo, createProject() implementa proteção single-flight, desabilita temporariamente os quatro cartões e apresenta status acessível da criação. O POST não é repetido automaticamente. Após confirmar ID, a abertura GET possui limite de 15 segundos por AbortController. Falha do GET mantém a criação e aponta o projeto por ID em Meus projetos; falha do POST orienta conferência antes de nova tentativa.
- JS SHA256 antigo cf3f9145eead024a7e4c3eca3034c283d4b38ae0a0c60e6a9f71cb2b70cfadcd.
- JS SHA256 atual 3b9f264dfa946fad348543376536a609e7a81efa00115bc0c6c16fde66cecd81.
- Backups privados Hostinger start-project-previous-20261119T142257Z.js e start-project-encoding-pre-20261119T142952Z.js.
- Original /estudio/ PHP SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf intacto.

## Provas
- Bun build do JavaScript de produção PASS, inclusive depois da normalização UTF-8.
- 37/37 unittest do plugin instalado PASS.
- Bun vm sintético com função real extraída do JS: 3 cenários PASS — rajada de três cliques gera 1 POST, GET indisponível conserva ID e mostra acesso em Meus projetos, erro de POST mostra alerta sem registrar projeto.
- Branch GitHub PR #338: Bun build PASS e manifesto QA 705/705 exactly once PASS no clone efêmero.
- Unit tests de branch: 93 testes com 7 falhas no primeiro ensaio; baseline #337 tinha as mesmas seis falhas antigas em navegação/CSS, e a falha adicional decorreu de asserção legada test_create_project_survives_detail_reload_failure que exigia literal const id e await reload(id). A asserção foi atualizada para as invariantes do fluxo seguro em commit 4267148e6c56162f4430ae506ccd85de3c2fb3c1. Nova execução da suíte expandida ainda sem recibo devido a falhas intermitentes de transporte remoto; registrar como não homologada.

## Restrições de integração e aceitação
Existem diferenças preexistentes entre o JavaScript do GitHub e o JS vivo em mensagens condicionais de retenção da lixeira e formatações. Preservar a produção atual e reconciliar essas diferenças antes do merge/deploy da árvore da PR #338. Teste visual autenticado no navegador do titular, após atualização forçada da página e acionamento de apenas um cartão, continua pendente. Homologação real do item 3 entre duas contas distintas continua pendente e foi limitada por recusas anteriores de segurança a testes de identidade simulada. Nenhum novo acesso, permissão nem credencial foi criado.
