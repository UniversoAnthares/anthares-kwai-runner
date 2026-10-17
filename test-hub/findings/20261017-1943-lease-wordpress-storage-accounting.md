# Lease WordPress video storage accounting correction
STATUS: RUNNING
AREA: wordpress-deploy
DATE: 2026-10-17
EXPIRES: 2026-10-17T20:13:00Z
BASELINE: anthares-wordpress GitHub main d1a7bf1808a5b227baf3fc54a44f7697aedcb1af; video-storage.php blob 4925c3f011fb0b00356a98d2cd0bb9e8b57697e4
PEER: GitLab main 6cba5f7c9eeec9c5fe4b5c658d9df1d7abb4eaed read; no blind mirror.
LIVE: SSH read production file matches 20 GiB hard cap and scans main + sandbox uploads. du uploads main 3934509091 bytes, sandbox 27747086983 bytes.
SCOPE: fix accounting/capacity, deploy isolated storage module atomically with rollback, reserve-release verification; no media deletion, no social publication.
SUCCESS: real storage status permits bounded new reservations with account margin; sandbox inventory separated; unit regression + PHP lint.
FAILED_AVOIDED: repeating CORTES E2E before fixing artificial shared-video cap. GitHub-masked digits are not literal 14.7 GB.
