# Lease isolado — correção CSS do /studio (item 1)
STATUS: RUNNING
AREA: anthares-studio-layout-css-only
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
START_UTC: 2026-11-16T21:20:00Z
EXPIRES_UTC: 2026-11-16T23:00:00Z
JOB: studio-css-page-id-fix-20261116
BASE: UniversoAnthares/anthares-wordpress test/studio-g4-parity-readonly-20261116
POLICY_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
SCOPE: exclusively new plugin body_class and page-scoped CSS selectors, unit tests, no original plugin changes.
ALLOW: isolated branch and draft PR. Live publication only with deployed-file SHA, backup, G1/G4 visual comparison and approval gates.
BLOCK: no edits to /estudio; no DB mutations; no enabling anst_writes_enabled; no merging other agents' branches; no arbitrary service reconfiguration.
PROOF: future CSS assets must contain zero page-id-19344 and post-19344 references, show layout full width with #sidebar-primary and #page-titlebar hidden only on studio, preserve dark theme.
ROLLBACK: revert isolated branch; live deployment must have prechange copies and straightforward revert.
