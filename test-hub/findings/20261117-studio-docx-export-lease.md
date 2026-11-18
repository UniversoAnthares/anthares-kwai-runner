STATUS: RUNNING
AREA: anthares-studio/includes/export/class-anst-docx-export.php;anthares-studio/anthares-estudio.php;anthares-studio/assets/estudio.js
OWNER: ChatGPT CURSO ESCRITA CRIATIVA
JOB: studio-p1-docx-export-20261117
BASELINE_PROVEN: new Studio plugin active, ACF runtime enabled, HEAD 16a08112797529e8a69551726595bc520cbf3d77, PHP ZIP extension available.
GOAL: Exportar DOCX autêntico, com capítulos ordenados e formatação do Delta; proteger metadados de revisão/relacionamentos e autoria. Não publicar manuscritos nem modificar dados do usuário.
SUCCESS_SIGNAL: endpoint privado GET export/docx, arquivo DOCX ZIP válido e botão na aba Publicação, deploy reversível.
FAILURE_SIGNAL: erro de PHP lint ou Word DOCX, abortar e restaurar arquivos.
TEST_VALIDITY: teste mínimo de estrutura ZIP e acesso backend via WP-CLI, sem bypass REST autenticado.
LEASE: 30 min, apenas 3 arquivos especificados, mesmo PR G4/G7.
