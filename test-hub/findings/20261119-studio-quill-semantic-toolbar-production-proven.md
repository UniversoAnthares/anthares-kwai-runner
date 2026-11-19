# Studio — seletor e controles semanticos fora do toolbar Quill

STATUS: PROVEN
AREA: wordpress/studio/quill-ui
DATE: 2026-11-19
RUN: Browserless /function, fixture isolada (sem usuario real)
JOB: Anthares Remote job 35fa04d3d7d3fb72d6a003d335b0d33c
COMMIT: UniversoAnthares/anthares-wordpress PR #336, head cd8f0c6f04f881377a50722a70314fb047638d9f
SUPERSEDES: none

## Escopo concluido
Implantado na Hostinger um hotfix minimo no novo plugin `anthares-studio`. O seletor `#aest-entity-select`, os botoes de vinculo/comentario e controles de classificacao de discurso passaram a pertencer ao grupo `.aest-editor-context-controls` externo ao `#aest-toolbar`. O toolbar Snow retem os controles nativos e a marcacao de pista. Estilos responsivos do grupo foram acrescentados ao CSS ja enfileirado pelo PHP, sem modificar seu carregador.

## Integridade e seguranca
- JS anterior SHA256: `4ebcaa2624f3f00b75e802fd45bbd3a8cccff52d85080300b767dc00a053dfee`.
- JS instalado SHA256: `cf3f9145eead024a7e4c3eca3034c283d4b38ae0a0c60e6a9f71cb2b70cfadcd`.
- CSS anterior SHA256: `c5252b834053a8434b01cc6ce0fee751baa81541f633ba9e62724ef08d6fe2dd`.
- CSS instalado SHA256: `938d5cdec7569206bd607a9565cef80ee41e6a23cb3cdc8cc478c5e5732ac470`.
- Original `/estudio/` preservado: PHP SHA256 `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.
- Backup anterior privado fora do public_html: `~/.anthares-studio-backups/quill-toolbar-20261119T043129Z`.
- Mutacao protegida por leitura atual, SHA esperado, lock privado, backup, escrita atomica e verificacao posterior.
- O registro de release do lease anterior aparece no comentario de 18/11 da PR Test Hub #2654.

## Testes comprovados
- Bun compilou o JS atualizado para browser: PASS.
- PHP 8.3 lint: PASS.
- QA Manifest em checkout da branch: `QA_MANIFEST_PREFLIGHT=PASS auditable=705 assigned=705 exactly_once=yes`.
- Browserless, Quill 2.0.3 real e dados sinteticos: seletor fora da toolbar e dentro do painel semantico, classificador acessivel e botoes nativos presentes: PASS.
- 40 reconstrucoes consecutivas das opcoes, seguidas de digitacao: PASS; zero excecoes JavaScript.
- Desfazer inicial nao alterou o capitulo carregado (Delta sintetico): PASS.
- Temas claro/escuro com cores computadas diferentes; mobile 390px com seletor visivel: PASS.
- Consulta publica da pagina e verificacao de hashes do plugin preservadas.

## Limites
PROVEN aplica-se ao defeito de UI/Quill reproduzido em fixture, codigo ativo e verificacao do DOM. Testes de gravacao REST autenticada com dois usuarios e homologacao integral do produto (G4-G8) permanecem independentes e nao foram declarados concluídos; as negativas previas de autorizacao foram respeitadas. A PR #336 e draft e depende da base #335; revisar diferencas de producao antes de qualquer merge/deploy futuro. Nenhum manuscrito real foi gravado.

## Consequencia
Nao recolocar `#aest-entity-select` dentro de `#aest-toolbar`. Preservar `studioHasQuill2()` e `editor.history.clear()` ao reconciliar a PR #336 com branches posteriores.
