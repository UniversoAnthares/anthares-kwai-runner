# Lease CORTES long finalization recovery audit
STATUS: RUNNING
AREA: queue
DATE: 2026-10-17
EXPIRES: 2026-10-17T19:44:00Z
BASELINE: anthares-clipper main 53ee6db152a36e580b17e418d8450c4118471e65
PEER: GitLab main 1b6d6dd95f49b2b30f563a4a6ae3445f8e6c0e9f lacks both long worker files; no mirror planned.
RUNS: 39055418321, 39057397351
SCOPE: long policy, storage preflight, retained local recovery, isolated unit tests; no publication or queue dispatch.
FAILED AVOIDED: 480-second floor and rendering before storage-full discovery.
SUCCESS: regression tests for accumulation, preservation and preflight; no remote publication claims.
