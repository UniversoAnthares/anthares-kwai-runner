# Lease — atualizar teste de integridade do CSS instalado no Anthares Studio
OWNER: ChatGPT / STUDIO_TEST_ISOLATION_20261119
STATUS: CLOSED_SUCCESS
SCOPE: somente `wp-content/plugins/anthares-studio/tests/test_isolation.py` na Hostinger.
START_UTC: 2026-11-19T23:54:00Z
EXPIRES_UTC: 2026-11-20T00:24:00Z
SOURCE: GitHub UniversoAnthares/anthares-wordpress main 075e525780064340f28eceb59b128ef4de5f13c8, arquivo tests/test_isolation.py blob cff8190fdbcce3367a9f2b34fe5da38fb67acb9c.
DEST_SHA256: 82dda09fe327887982c1860a06deeaf253d86b716f82441d6422ecf61dfcb83b.
CSS_VALIDATION: assets/estudio.css Git SHA 2970b994b48314c319f86b0a8f3b661ab9976c32 corresponde exatamente ao GitHub main.
CAUSALITY: teste antigo exige hash CSS 98b834..., mas arquivo legítimo mudou; teste main substitui comparação binária por verificação semântica de seletores e isolamento, mantendo SHA dos assets de terceiros.
GUARDS: apenas 1 arquivo de teste; cópia privada e SHA contra edição concorrente, sem alterar /estudio ou dados; nova versão só com validação; rejeitar HEAD GitHub alterado.
ACCEPTANCE: 37 testes antigos com 1 falha antes; após substituição executar unittest discover; reportar contagem e falhas, preservar integridade do site.

CLOSED_UTC: 2026-11-19T23:56:15Z
PRODUCTION_RESULT: Hostinger test_isolation.py blob cff8190fdbcce3367a9f2b34fe5da38fb67acb9c; CSS blob 2970b994b48314c319f86b0a8f3b661ab9976c32; 51/51 Python tests PASS; PHP lint both files PASS; /studio HTTP 200. Original test SHA256 82dda09fe327887982c1860a06deeaf253d86b716f82441d6422ecf61dfcb83b preserved in private backup on Hostinger. No legacy /estudio modification; no user data mutation.
