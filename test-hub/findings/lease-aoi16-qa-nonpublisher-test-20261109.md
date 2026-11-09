# AOI #16 — excluir falhas de testes estáticos do QA de publicações
STATUS: RUNNING
AREA: qa-p0-nonpublisher-static-test-classification
DATE_UTC: 2026-11-09
ITEMS: [16]
OWNER: chatgpt-aoi16-static-false-p0-20261109
LEASE_SCOPE: tools/cortes_qa_p0_router.py; .github/workflows/cortes-qa-p0-publication-watchdog.yml; tests/test_cortes_qa_p0_router.py; related historical issue #653
LEASE_EXPIRES_UTC: 2026-11-09T03:08:00Z
BASE_HEAD: a8e58a02cec247406779546ce45856f643480606
GOVERNANCE_VERSION: 223433740e807a90
BASELINE_PROVEN: GitHub issue #653 classifies run 39777379607 as publication-failure. Original workflow test-cortes-cycle-policy.yml at run SHA 0bbcd4af only performs pip install + pytest, has contents:read, no media or publisher. Two QA scan paths use broad name tokens and do not exclude static tests. Earlier PR #2015 excluded watchdog/preflight classes and is merged.
FAILED_AVOIDED: do not re-run failed publishing; no media, account changes, queue changes, no Windows, no blanket closure of real continuity incidents, no fallback through denied channels.
SUCCESS_SIGNAL: both QA scanner filters omit exactly verified nonpublisher test/policy workflow classes while retaining real TikTok/Pinterest/Kwai publisher failures; static regression passes; source merged if review approved; historical #653 retitled/closed precisely as false *publication* category only.
FAILURE_SIGNAL: a real publisher gets excluded; test regression; concurrent file owner; moving main head; source conflict.
TEST_VALIDITY: fixture-only Python unittest/JS regex and read-only original Actions metadata; no live public posts or receipts asserted.
ROLLBACK: revert only classification change.
