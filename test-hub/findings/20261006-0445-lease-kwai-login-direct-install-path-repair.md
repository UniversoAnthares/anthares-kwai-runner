# Lease: kwai-login direct install harness repair
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
LEASE_AREA: kwai-login
LEASE_EXPIRES: 2026-10-06T05:15:00Z
BASELINE_PROVEN: CircleCI Android executor boots; validated Kwai split bundle exists; run 37414878850 reached SDK installation and failed before ADB because platform-tools was not on PATH.
FAILED_AVOIDED: discarded bare ikwai://login/authorization routes and GitHub harnesses that fail before ADB are not reused. This repair changes the observed harness cause by exporting platform-tools explicitly.
SUCCESS_SIGNAL: BOOT_OK followed by KWAI_DIRECT_INSTALL_OK on the same GitHub runner.
FAILURE_SIGNAL: bounded emulator/ADB/install failure after adb is resolvable.
TEST_VALIDITY: absence of adb after explicit platform-tools PATH is harness invalid; install failure after BOOT_OK is valid install evidence; no authentication conclusion is drawn from install-only failure.
