# Studio G4/G6 - Quill 2.x obrigatorio, protecao contra biblioteca global legada
STATUS: RUNNING
AREA: anthares-studio/editor/quill-version
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-quill2-global-guard-20261118
POLICY_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
WORDPRESS_BRANCH: fix/studio-quill2-version-guard-20261118
BASE: fix/studio-five-global-nav-qa-20261118 HEAD 23e921ebbc6ab2ba8f6d28779ae9b282edb239b8
SCOPE: Exclusivamente anthares-studio/assets/estudio.js. O original /estudio nao sera tocado. Impedir que a biblioteca global Quill 1.3.6 do WordPress satisfaça o requisito Quill 2.x. Carregar o Quill 2.0.3 local e validar major ao concluir.
EVIDENCE: Headless Chrome isolado em 18/11 reproduziu TypeError ao inserir texto, com stack em https://cdn.quilljs.com/1.3.6/quill.min.js?ver=7.1.4. Codigo live loadQuill() retorna Promise.resolve() para qualquer window.Quill e setupEditor() usa a mesma condicao.
QA: Node --check, comparacao de endpoints sem escrita, Chrome headless com fixture de Quill 2.x, hash do plugin original antes/depois.
ROLLBACK: backup privado byte a byte do JS anterior e restauracao atomica controlada por hash.
