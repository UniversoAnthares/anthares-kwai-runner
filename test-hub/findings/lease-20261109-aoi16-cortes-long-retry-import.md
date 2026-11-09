# AOI #16 — lease: corrigir importação do retry longo CORTES
STATUS: RUNNING
AREA: qa-p0-cortes-long-retry-module-import
ITEMS: [16]
DATE_UTC: 2026-11-09T01:38:03.090Z
EXPIRES_UTC: 2026-11-09T02:08:03.090Z
OWNER: chatgpt-aoi16-cortes-long-retry-20261109
BASELINE_PROVEN: Clipper main 18aa437f90430a6c840444092e95b0d81ee7c1ae; qa/cortes_long_retry_guard.py blob 6de8487b45a48388875354a3a39235f3808fc317; GitLab peer same content. Original GitHub jobs 120196022003 and 124135466726 stopped at admission on ModuleNotFoundError cortes_source_adapter, before processing/media.
FAILED_AVOIDED: no reexecution of PC/self-hosted workflows, no publication, no queue writes, no secret, no change to scheduler, no production service.
SUCCESS_SIGNAL: import path from direct execution qa/cortes_long_retry_guard.py resolves root module with minimal isolated patch and nonpublishing regression proof.
FAILURE_SIGNAL: preexisting concurrent lease, changed file SHA or policy refusal prevents write; abort without retry.
TEST_VALIDITY: test import/compile only, without WordPress, Neon or social effects.
RELATED_INCIDENTS: https://github.com/UniversoAnthares/anthares-kwai-runner/issues/1145 ; https://github.com/UniversoAnthares/anthares-kwai-runner/issues/1982
