# Android redundancy candidates — provider audit
STATUS: PARTIAL
AREA: android
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: test-hub/findings/20261006-0852-lease-android-redundancy-research.md

## Objetivo
Find independent no-PC Android substrates without disturbing the active kwai-login lease.

## Resultado
Two sustainable candidates remain worth integration:
1. Firebase Test Lab Spark: 10 virtual + 5 physical test runs/day at no cost. Instrumentation tests can run up to 60 min virtual / 45 min physical, with uploaded app/test APK and device results. Strong candidate for ANDROID_SECONDARY; session persistence across separate runs is weak, so login+post must fit one run or state must be externally restored.
2. Cirrus CI for public/open-source projects: provider documents free Linux/ARM builds for open source and an Android hardware-accelerated emulator recipe with kvm:true, adb and artifacts/logs. Strong candidate for ANDROID_TERTIARY and causally independent from GitHub/CircleCI.

Additional candidates:
- Bitrise Hobby is free with 300 credits/month and 90-min build timeout; its Virtual Device Testing is Firebase-backed, so it adds orchestration redundancy but not a causally independent Android substrate.
- Genymotion SaaS supports ADB/CI and is ARM64, but recurring cloud use is paid ($0.06/min); free access is trial-only.
- BrowserStack App Automate and AWS Device Farm provide useful real-device trials, but their free quotas are trials rather than sustainable recurring free infrastructure.
- Sauce Labs trial supports real devices/Appium and limited ADB, but free-trial restrictions make it unsuitable as a permanent free tertiary.

## Bloqueio concreto
Firebase requires a Firebase/GCP project and credentials; Cirrus requires connecting the public repository to a Cirrus account/app. Neither credential is currently exposed to this agent. Because kwai-login is actively leased, no competing login harness mutation was made.

## Consequência
Keep current GitHub path as ANDROID_PRIMARY. Integrate Firebase Test Lab first as ANDROID_SECONDARY when project credentials exist. Integrate Cirrus KVM as ANDROID_TERTIARY when the repository is connected. Bitrise is a fourth orchestration fallback, with Firebase substrate dependence explicitly recorded.
