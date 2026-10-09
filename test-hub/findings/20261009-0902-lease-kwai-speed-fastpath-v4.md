# Lease — Kwai speed fast path v4 continued optimization
STATUS: RUNNING
AREA: kwai-speed
DATE: 2026-10-09
RUN: active probes 37933405989; 37933472809
COMMIT: baseline 52b884c5ac3b2302d1802802ed67dff5eaafdfae / 38cc8453ee49825da16455c936e96db325c209ad
SUPERSEDES: 20261009-0832-lease-kwai-speed-fastpath-v3.md
LEASE_START: 2026-10-09T09:02:00-04:00
LEASE_EXPIRES: 2026-10-09T09:32:00-04:00

## Objetivo
Continuar reduzindo o tempo total do fast path Android preservando o snapshot cross-run kwai-ready real em menos de 10 s, sem alterar login, sessão ou publicação.

## BASELINE_PROVEN
Slim AVD v4 cache `kwai-speed-avd-direct-slim-android35-v4`: cache ~1.760 GB, independent runner true snapshot load, boot 5 s, total observed 45 s. Direct v3 best observed total 42 s; v4 structurally saves ~953 MB versus v3. API35 system image cache v1 and emulator v1 remain required.

## FAILED_AVOIDED
Do not retry snapshot-only archive; removing userdata-qemu.img.qcow2 or cache.img.qcow2; AOSP ATD API30; sdkmanager cold install; or system image NOTICE/data replacement cache. These paths were measured and rejected or too small to matter.

## ACTIVE CAUSAL TESTS
1. Delete only internal QCOW snapshot tag `default_boot`, retaining all QCOW files and `kwai-ready`, then measure true load and compressed potential.
2. Probe headless emulator pruning (`lib64/qt`, `resources`) without creating cache first.

## SUCCESS_SIGNAL
True `Successfully loaded snapshot 'kwai-ready'`, no cold-boot fallback, boot <10 s, and material cache-byte reduction. Only then may a replacement cache be created and validated on another hosted runner.

## FAILURE_SIGNAL
Any failed snapshot load, cold boot fallback, missing runtime dependency, boot >=10 s, or savings too small to justify quota pressure.

## TEST_VALIDITY
GitHub-hosted runner only, distinct runner validation before PROVEN, /dev/kvm enabled, exact snapshot-load log required. Harness/cache failures are not snapshot failures.

## Coordenação
Scope limited to kwai-speed isolated workflows and append-only findings. Never edit kwai-login agent files. No local PC.
