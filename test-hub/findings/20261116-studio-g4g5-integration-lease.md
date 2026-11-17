# Coordenação — G4 homologação e G5 ACF+navegação final
STATUS: RUNNING
AREA: studio-g4-visual-and-g5-acf-navigation-integration
DATE: 2026-11-16
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g4g5-20261116
BASELINE_PROVEN:
- /studio privado ID 21383 WordPress 7.1.4, plugin 0.7.8-staging ativo.
- Original PHP SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf
- Clone PHP SHA256 042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7
- CSS clone SHA256 6fc81afb986db6c427da558fd6ed13218575ea90446cbabd0400a9f8e827de97, dark 2917c1acbfa82098989915b7f1725b729d6345fe920a71398b19f4757563435b.
- Item 3, 71 pares, 7 Quill, zero divergências, SHA source efbe0aea9f69979ec0122239329d7471c6370092718f845f3bd3a8a4833fea8c.
- PR #310 G4 hotfix, PR #311 G5 ACF, PR #312 G6 nav, PR #313 CSS page scope.
FAILED_AVOIDED:
- Nunca reverter hotfix de restauração/lixeira, CSS scoped ou dados, nem mesclar source desatualizado diretamente em produção.
- Nunca usar sessão do navegador pessoal, exportar cookies ou contornar login. Autenticar usuário sintético apenas em banco isolado.
SUCCESS_SIGNAL: C001-C025 com evidências dinâmicas no WP isolado e screenshots desktop/mobile, equivalência visual real; G5 migrador idempotente 414 valores/ACF ON e OFF; cinco globais/sete grupos internos navegáveis e testados; publicação apenas após gates.
FAILURE_SIGNAL: diferença visual crítica, quebra de autorização/Delta, 71 pares divergentes, duplicatas, URI incorreta, QA falho.
TEST_VALIDITY: SQL em cópia isolada sem rede, controle de usuário sintético, screenshots sanitizadas, WP live somente leitura; source e deployed SHA separados.
SCOPE: plugin novo anthares-studio/ em branch exclusiva; documentos e testes. Nenhum original anthares-estudio, código CORTES ou dados live.
ROLLBACK: qualquer publicação live exige backup privado comprovado e restauração atômica, sem habilitar escrita antes dos gates.
