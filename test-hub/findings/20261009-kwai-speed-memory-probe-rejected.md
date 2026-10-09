# Kwai speed lower-memory snapshot probe
STATUS: FAILED
AREA: kwai-speed
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37935222568
JOB: 113835469928
COMMIT: ce9691d0e9341626009001b54ee3d468b8b5a544
SUPERSEDES: none

## Hypothesis
Lowering emulator RAM from the 2048 MB baseline to 1024 or 1536 MB might shrink the quickboot RAM snapshot and therefore the AVD cache.

## 1024 MB
Cold boot 38 s; snapshot save 3 s; ram.bin 1,323,835,723 bytes; snapshot directory 1,328,415,035 bytes; AVD raw 2,239,807,292 bytes. True kwai-ready load succeeded in 5 s; emulator log: `Successfully loaded snapshot 'kwai-ready' using 2426 ms`. Compressed AVD tar = 1,776,827,395 bytes.

## 1536 MB
Cold boot 37 s; snapshot save 4 s; ram.bin 1,342,269,371 bytes; snapshot directory 1,346,928,464 bytes; AVD raw 2,325,822,815 bytes. True kwai-ready load succeeded in 5 s; emulator log: `Successfully loaded snapshot 'kwai-ready' using 2543 ms`. Compressed AVD tar = 1,782,887,897 bytes.

## Decision
Do not create lower-memory cache variants. The current slim AVD v4 cache is 1,760,052,245 bytes, smaller than either probe. Lowering configured RAM does not materially shrink this quickboot snapshot representation and does not improve the cache payload.

## Next causal experiment
Keep 2048 MB RAM and reduce the AVD data/cache partition sizes at creation time, because userdata-qemu.img.qcow2 and cache.img.qcow2 are required for snapshot load but their physical sizes may be reduced by smaller backing partitions. Validate true snapshot load and compressed size before saving any new cache.

## Coordination
Only kwai-speed isolated workflow/finding. No login agent change. No local PC.
