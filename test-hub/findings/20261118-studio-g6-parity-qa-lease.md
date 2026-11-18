STATUS: RUNNING
AREA: anthares-wordpress/anthares-studio/tests/test_g6_fixed_navigation.py
OWNER: ChatGPT CURSO ESCRITA CRIATIVA
JOB: studio-g6-parity-qa-20261118
BASE: UniversoAnthares/anthares-wordpress fix/studio-pilot-fallback-safety-20261117 @ ac0e9b1e384a06fc1a861802fdc1c647e7cdead7
SOURCE: Test Hub branch coord/studio-pilot-fallback-20261117 @ 9fcdb0941291afc5fd3824e1b95159b84436f3e5
PURPOSE: fix a verified stale legacy-action set assertion: current JS declares 18 literal actions while G6 test expects exact 14 original actions. Preserve 14 original actions and assert new functional actions independently. Isolate branch and do not modify production, legacy plugin, DB, ACF flags or active PR branches.
PEER: GitLab project UniversoAnthares/anthares-wordpress has no matching studio work branch in list_branches query.
TEST: Python unittest from isolated checkout, JS syntax and QA manifest checks where available.
LEASE: confined to new isolated GitHub branch, expires after 30 minutes; record closure outcome.
