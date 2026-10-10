# AI Commander recovery: read-only diagnostic checklist
# The PC-side agent must be explicitly authorized and healthy before any remote execution.
# Do not disable antivirus, modify quarantine, access browser secrets, or bypass security blocks.
# Observed 2026-10-10:
# - AI Commander 1.4.1 install.log verified 80/80 files on 2026-10-07.
# - 1.4.2 unattended update started 2026-10-10 12:07:40, log ended mid-install.
# - AI Commander connector lists aic-lucas-pc offline.
# - MeshCentral listed DESKTOP-FTDK0HP connected; remote execution blocked.
# - Desktop Commander device online; command execution unavailable due monthly quota.
#
# Authorized operator recovery procedure:
# 1. Obtain official signed AI Commander installer from publisher.
# 2. Validate Authenticode publisher and installer hash before repair.
# 3. Inspect Windows event logs, AV quarantine metadata, install manifest.
# 4. Repair via vendor installer only with user-authorized local execution.
# 5. Confirm device online using AI Commander list_machines.
# 6. Only then run official Browserless profile sync, tiktok.com only.
#
# Never upload Chrome profiles, cookies, browser secrets, or credentials to CI artifacts.
