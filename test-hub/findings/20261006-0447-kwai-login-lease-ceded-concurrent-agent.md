# Kwai-login lease ceded after concurrent Agent mutation
STATUS: SUPERSEDED
AREA: kwai-login
DATE: 2026-10-06
SUPERSEDES: test-hub/findings/20261006-0445-lease-kwai-login-direct-install-path-repair.md

## Resultado
The leased direct-install repair completed PROVEN in run 37415036743 with BOOT_OK, install Success, and KWAI_DIRECT_INSTALL_OK.

After that proof, HEAD advanced to commit 20ec01dd9b3de94358a6b1dbb577c305e4bb1cb5, which mutates android-agent-runtime AccessibilityService diagnostics in the same kwai-login causal area. Under the shared lease protocol this CHAT2 lease now yields before any authentication-surface mutation.

## Consequência
Preserve the proven remote install baseline. Do not start a competing kwai-login experiment while the newer Agent runtime chain is being mutated/run. kwai-publish promotion remains fail-closed until independent READY.
