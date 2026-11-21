# Anthares Studio — Itens 8 e 9: linha do tempo e Jornada do Herói

**Data:** 20/11/2026 (America/Campo_Grande)  
**Situação:** implantados no WordPress `/studio/`, com verificação de integridade e QA real.

## Funcionalidades entregues

**Manuscrito e Jornada:** cada capítulo continua podendo ser criado diretamente no Manuscrito. O sistema identifica os modelos efetivamente utilizados, exibindo o aviso `Fora da estrutura` e o seletor de etapa dentro da lista de capítulos e do editor somente quando existe pelo menos um capítulo classificado naquele modelo. Os capítulos anteriores podem ser arrastados da área de disponíveis para qualquer etapa ou vinculados pelo formulário. É possível criar capítulos dentro da etapa; a mesma entidade `anst_capitulo` aparece no Manuscrito. Uma etapa comporta inúmeros capítulos. O modelo de doze etapas mantém opções de reorganizar a sequência de estágios e ocultá-los/reexibi-los sem apagar associações.

**Cenas e acontecimentos:** cadastros em CPT canônico `anst_cena` ou `anst_evento`, mantendo IDs persistentes. Uma cena dramatizada e um acontecimento resumido (por exemplo, viagem de seis meses) podem referir-se ao mesmo capítulo e ter etapas da Jornada diferentes da classificação geral do capítulo. O acontecimento herda a etapa do capítulo quando não há etapa específica.

**Tempo e apresentação:** a ordem de apresentação é obtida dos capítulos na ordem real do Manuscrito, com refinamento opcional dentro do capítulo; a cronologia é independente. O autor pode definir data ISO histórica ou período livre, posição manual com arraste, ou referência anterior, posterior ou simultânea a outro evento, incluindo quantidades explícitas de dias, semanas, meses e anos. Referências cíclicas são recusadas. São oferecidos exatamente **dois** modos de exibição: ordem de apresentação e ordem cronológica. O modo de comparação simultânea sugerido anteriormente foi descartado a pedido do titular.

**Visualização:** uma linha horizontal de acontecimentos no modo escolhido, com vínculos a cenas, capítulos e etapas; na parte de análises, gráfico de tensão planejada registrada pelo autor, relacionado a eventos e etapas. Fichas originais podem ser abertas diretamente. Alterações de etapas e de cronologia têm histórico limitado a 25 estados e recurso de recuperação.

## Operação, provas e arquivos

**PRs:** https://github.com/UniversoAnthares/anthares-wordpress/pull/395 e https://github.com/UniversoAnthares/anthares-wordpress/pull/396  
**Revisões integradas:** `643c1218233c3012e091142a9f58356c2050bf68` e `afdfb42930a3c97762ea4053c064ba6c5cdc34e1`.

Hashes de código instalado iguais ao repositório:
- `anthares-studio/anthares-estudio.php`: `78ba7f32cbda7ad34f54bf5c41a9fc7cb71d2920`
- `anthares-studio/assets/estudio.js`: `e2498bc6dd5e9ae473f7e4ffb2abdb4ed37a000d`
- `anthares-studio/assets/studio-g7-workspaces.js`: `172bb0d3cfee523bbb1d41456d434f511b8d27d4`
- `anthares-studio/includes/domain/class-anst-narrative-timeline.php`: `0e19a4ffeda37c02eacd3d4a06b2a4ce197a6ce3`
- `anthares-studio/assets/studio-narrative-timeline.js`: `f7b4ea41bcf52e158a74e1c221fc809a1103a3eb`
- `anthares-studio/assets/studio-narrative-timeline.css`: `31733d24dbfdd7dd87f35ca11dcd44ff1a5e8b76`

**QA:** 26/26 verificações de integração em WordPress e ACF habilitado, com duas identidades distintas, usando banco de dados InnoDB, START TRANSACTION / ROLLBACK, sem retenção dos projetos de teste. Abrange capítulos, criação idempotente e isolamento das cenas/eventos, herança ou substituição de estágio, cronologia ISO, relativa de três dias, bloqueio de ciclo, movimentação de ambos os tipos de linha, persistência/histórico/restauração, ordem/visibilidade dos estágios e bloqueio de escrita entre contas.

**Integridade:** três arquivos originalmente presentes receberam backups em `/home/u566597497/domains/anthares.us/studio-private-backups/20261120-items8-9/`, versões intermediárias de PHP/JS relativos em subpasta `relative-intervals/`, tudo fora de `public_html`. Deploy só após comparação SHA antes/depois, PHP 8.3 `-l` e `node --check`. `/studio/`, `/estudio/`, JS e CSS retornaram HTTP 200; plugin ativo. Manifestos QA iguais e cobertura 740/740 arquivos auditáveis.

## Pendência de homologação

Execução autenticada do fluxo visual no navegador de um cliente e homologação com público real continuam atribuídas ao item 21. Os testes de modelo, persistência, permissões e regressões em WordPress já foram concluídos; um HTTP 200 sozinho não foi usado como comprovação visual de interface.

**Status de engenharia:** itens 8 e 9 publicados em produção; aceite de usabilidade completo condicionado ao item 21.
