# Eight-repository content parity and Asaas PHP regression QA
STATUS: PROVEN
AREA: git-provider-content-parity-and-asaas-isolated-tests
DATE: 2026-10-08
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2927111773
JOB: 17035374009
COMMIT: d71a3490b5ab7bcbdee792e2f52bfb6eb95404fb
SUPERSEDES: 20261008-eight-repo-ref-parity-readonly-audit.md (tree parity); 20261008-asaas-isolated-php-functional-six-tests-and-provider-guard.md (follow-up CI)

Eight repos assessed: anthares-clipper, anthares-wordpress, anthares-kwai-runner, anthares-transcricao, anthares-telegram-relay, github-slideshow, wiki, home. WordPress and github-slideshow main refs matched by SHA. Clipper, transcricao, telegram-relay, wiki and home were freshly fetched from both providers and `FETCH_HEAD^{tree}` compared: all five TREE_MATCH=True. Kwai-runner main was safely fast-forwarded from GitHub to GitLab SHA 4cb15bec6cef0e9190c9e4ccdc7252a1f1f7e76e after ancestry check; thus same main ref and tree at the check. Result: eight repo content trees match at observation time. Different SHA for five repos reflects history divergence, not differing file content. No force pushes or rewriting independent histories.

Asaas WordPress PR18 https://github.com/UniversoAnthares/anthares-wordpress/pull/18 branch fix/asaas-webhook-failclosed-20261008 SHA d71a3490b5ab7bcbdee792e2f52bfb6eb95404fb mirrored to GitLab. GitLab pipeline 2927111773 final status SUCCESS, job 17035374009 trace `PASS existing`, `PASS corrupt`, `PASS decrypt-fail`, `PASS encrypt-fail`, `PASS write-fail`, `PASS new-token`, `ASAAS_WEBHOOK_TOKEN_REGRESSION=PROVEN`, `GITLAB_WORDPRESS_QA=PROVEN`, `Job succeeded`. Additional static assertions guard against deleting an existing webhook, configuring an unverified provider token, or proceeding after webhook listing fails. No live Asaas calls, no production deployment, no financial operations. The tests are isolated mock-based functional tests, not full provider integration tests.
