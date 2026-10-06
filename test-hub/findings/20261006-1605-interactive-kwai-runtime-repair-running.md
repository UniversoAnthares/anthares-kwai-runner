# Execution — interactive Kwai runtime repair promoted
STATUS: RUNNING
DATE: 2026-10-06
AREA: kwai-login

ACTION:
- Patched .github/workflows/kwai-interactive-remote-login.yml at commit 6b51ca8d2d88beff9eaff899d3a016119f648c46.
- Root cause was proven in run 37487133042: the workflow exited 127 during Android SDK preparation because it assumed $ANDROID_HOME tooling paths.
- Patch now explicitly sets ANDROID_SDK_HOME=$HOME/.android and ANDROID_AVD_HOME=$ANDROID_SDK_HOME/avd, discovers sdkmanager/avdmanager/emulator/adb from SDK_ROOT, exports executable directories, and bounds adb wait.
- New run 37492845981 is active. Prepare Android SDK is currently running; no competing Kwai login run should be started.

CLOSED:
- Login surface and semantic selector QA15.
- READY gate/promotion QA.
- Control-plane items 1-5.
- TikTok Sandbox OAuth + private Direct Post is PROVEN separately; do not repeat its authorization or reuse the same private video.

NEXT GATE:
- If this runtime reaches the interactive owner-login step, the remaining external boundary is the legitimate Kwai account authentication/authorization. No challenge bypass.
- On fresh authenticated READY evidence, use the already-proven READY barrier and canonical one-job executor for exactly one serialized canary.

SUCCESS_SIGNAL:
REAL_KWAI_READY with exact account identity, fresh proof_id and restored authenticated state.

FAILURE_SIGNAL:
SDK/AVD failure after this causal repair, missing required secret, or owner authentication cannot complete.

DO NOT:
repeat old emulator-path variants, create a 30-way login matrix, or claim real publication from synthetic/control-plane QA.