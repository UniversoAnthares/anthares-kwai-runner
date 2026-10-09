# Kwai speed parallel-cache v5 proven
STATUS: PROVEN
AREA: kwai-speed
DATE: 2026-10-09
RUN_PARALLEL: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37934754983
JOB_PARALLEL: 113833904161
RUN_SEQUENTIAL_CONTROL: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37934873754
JOB_SEQUENTIAL_CONTROL: 113834309103
COMMIT: 0f50bbe0429676d89a9b409dc19c5f7cdf49c5a2
SUPERSEDES: none

## PROVEN COMPONENTS
AVD cache `kwai-speed-avd-direct-slim-android35-v4` = 1,760,052,245 bytes. Android image cache `kwai-speed-android35-google-apis-x86_64-v1` = 1,648,521,220 bytes. Slim headless emulator cache `kwai-speed-emulator-headless-x86_64-v2` = 122,635,253 bytes; built by removing lib64/qt, resources and unused non-x86_64-headless QEMU binaries from emulator v1. The slim emulator was previously validated with true kwai-ready snapshot load and 4 s boot.

## PARALLEL RESULT
Run 37934754983 completed SUCCESS on GitHub-hosted runner westus, Worker ID 6985746e-5ebb-4444-88bd-cc69385345cb. All three cache lookups hit. The three restores ran concurrently inside actions/github-script@v8, which receives the ephemeral Actions cache runtime context without exposing token values.

Measured child times: AVD 24 s; Android image 31 s; slim emulator 4 s. `PARALLEL_RESTORE_SECONDS=31`. After restore: `V5_SNAPSHOT_BOOT_SECONDS=6`, `V5_ACTUAL_LOAD=true`, emulator log `Successfully loaded snapshot 'kwai-ready' using 2375 ms`, `V5_TOTAL_SECONDS=40`, `V5_RESULT=PROVEN_SUB10`.

## A/B CONTROL
Sequential control run 37934873754 used the exact same AVD v4, image v1 and emulator slim v2. It completed SUCCESS: `SEQ_RESTORE_SECONDS=46`, `SEQ_SNAPSHOT_BOOT_SECONDS=5`, `SEQ_ACTUAL_LOAD=true`, snapshot load 2203 ms, `SEQ_TOTAL_SECONDS=51`, `SEQ_RESULT=PROVEN_SUB10`.

## IMPROVEMENT
Parallel cache restore reduces measured restore wall-clock from 46 s to 31 s (-15 s, ~32.6%) and total path from 51 s to 40 s (-11 s, ~21.6%) in the A/B sample while preserving real snapshot load. It also beats the previous best total of 42 s from direct v3.

## FAILED / FIXED HARNESS PATHS
Direct invocation of actions/cache from a normal shell is invalid because ACTIONS_RUNTIME_TOKEN/ACTIONS_RESULTS_URL are not exposed to run steps. Moving invocation into a JavaScript action context exposed the runtime correctly. Initial AVD child miss was not eviction: inventory run 37934604405 proved all cache keys exist. Root cause was cache version mismatch because v4 was saved with literal `~/.android/...` path inputs while the child queried absolute `/home/runner/...` paths. Matching the original path strings fixed the version and restored all three caches concurrently.

## NEXT
Preserve parallel v5 as the current best proven fast path. Next optimization should reduce the dominant payloads themselves. The largest reducible candidate is snapshot RAM; test lower emulator memory (1024/1536 MB) locally first, measure true snapshot load and compressed AVD size, and create a replacement cache only if materially smaller and stable.

## COORDINATION
Only kwai-speed isolated workflows/findings changed. No kwai-login files altered. No local PC used.
