# Android 30 ARM64 system image already contains vbmeta + super
STATUS: PROVEN
AREA: kwai-arm64-runtime
DATE: 2026-10-12
PIPELINE: https://gitlab.com/universo-anthares-group/anthares-kwai-runner/-/pipelines/2940639487
JOB: 17127002330

## Evidence
Independent inspection of `system-images;android-30;default;arm64-v8a/system.img` shows a raw GPT disk with:
- partition 1 `vbmeta`, sectors 2048-4095, 1 MiB;
- partition 2 `super`, sectors 4096-6311935, ~3.0 GiB.

The package separately includes `vendor.img`, whose GPT partition is named `vendor`.

Signal: `ARM64_SYSTEM_LAYOUT_FORENSICS=PASS`.

## Consequence
The missing first-stage boundary is not absence of a `super` container. The logical-partition source is already present in `system.img`. Combined with the recovered vendor `fstab.ranchu` and AOSP first-stage rules, the next minimal test is to place that fstab in the first-stage ramdisk so init can discover `super`, create dm-linear logical partitions, and mount metadata before proceeding.
