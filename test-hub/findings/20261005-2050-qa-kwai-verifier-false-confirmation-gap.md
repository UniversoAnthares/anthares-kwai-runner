# Kwai verifier can falsely confirm unrelated recent post
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: none
JOB: read-only code audit
COMMIT: none
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2047-qa-kwai-profile-loading-reconcile-rule.md; current kwai_verify_publication.py.
FAILED_AVOIDED: no publication triggered; no mutation under kwai-publish lease; no Home/toast treated as final confirmation.
SUCCESS_SIGNAL: verifier binds confirmation to the intended job/media/post identity and stable correct-account Profile.
FAILURE_SIGNAL: generic freshness marker can return success without matching intended title/media identity.
TEST_VALIDITY: direct source audit of current main.

## Resultado
O verifier atual aceita qualquer UI contendo published/publicado/just now/agora, mesmo sem vincular esse marcador ao título ou ao media/job esperado. Assim, um post anterior recente pode produzir falso CONFIRMED. Além disso, a navegação quebra após a primeira tentativa mesmo se Profile não tiver sido realmente tocado, e não distingue PROFILE_LOADING/READY/UNAVAILABLE conforme a regra já consolidada.

## Evidência decisiva
kwai_verify_publication.py retorna 0 quando encontra qualquer um dos marcadores genéricos de recência, sem exigir correspondência do título/job/media. O loop de Profile contém break externo incondicional após a primeira iteração bem formada.

## Consequência
Antes do canário real, o Chat 2 deve exigir identidade positiva do post pretendido (título/remote id/evidência específica) e identidade da conta, modelar PROFILE_LOADING/READY/UNAVAILABLE e manter ambiguidade como UNCERTAIN. Marcador genérico de recência não pode fechar ledger.