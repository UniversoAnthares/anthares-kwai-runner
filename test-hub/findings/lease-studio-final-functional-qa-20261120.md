# Lease — homologação funcional Anthares Studio
OWNER: ChatGPT / STUDIO_FINAL_E2E_QA_20261120
STATUS: CLOSED_PARTIAL_AUTH_UI_REQUIRED
START_UTC: 2026-11-20T00:09:00Z
EXPIRES_UTC: 2026-11-20T00:39:00Z
SCOPE: QA de /studio em produção, WordPress REST server-side e interface existente. Somente fixtures temporárias sob transação ROLLBACK; sem dados de clientes, sem cobranças ou publicações. Falhas de UI são inspecionadas sem alterar /estudio.
BASELINE: plugin 0.7.8-staging ativo; Python 51/51 PASS; GitHub main 075e525780064340f28eceb59b128ef4de5f13c8; browser AntharesWordPressAdmin port 9234 mostra aest-access-gate (sessão autenticada indisponível).
GUARDS: preservar o plugin legado e dados reais; sem login de conta real contornado, nem token/cookie/senha expostos; bloquear e-mails externos nos testes; verificar limite de execução, liberar locks e sessões próprias; relatar separadamente testes de rotas e E2E real.
SUCCESS: rotas GET/POST avaliadas com fixtures transacionais e rollback confirmado; permissões negadas a anônimos; páginas desktop/mobile conferidas; evidência objetiva de lacunas.
FAILURE: se houver fuga de estado/efeito inesperado, interromper e registrar incidente.

CLOSED_UTC: 2026-11-20T00:26:00Z
EVIDENCE: test-hub/findings/20261120-studio-final-functional-qa-partial.md. 54 REST verification lines PASS, InnoDB rollback confirmed (0 persisted test posts), PHP lint pass, 14/14 JS parse, live public login gate. Authenticated browser UI unavailable due logged-out profile; test user creation explicitly blocked; no circumvention or production mutation. Lease released.
