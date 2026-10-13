# ARM64 VDC Matrix 40 — /data device fixed, failure moved earlier to first-stage init
STATUS: FAILED_CAUSAL_BOUNDARY
AREA: kwai-arm64-runtime
DATE: 2026-10-12
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38331388423
REPRESENTATIVE_JOBS: order-0=115081673421; order-6=115081673377

## Result
The VDC matrix successfully corrected the earlier userdata premise. A real 4 GiB ext4 filesystem is present as kernel device `vdc`:

- vda = ~49 MiB disk
- vdb = ~3.01 GiB disk
- vdc = 4.00 GiB ext4 data disk
- vdd = 192 MiB metadata GPT disk

Nevertheless both baseline `order-0` and `order-6` (`androidboot.boot_devices=a003c00.virtio_mmio`) fail identically before Android init second stage.

Observed sequence:
- `init first stage started!`
- virtio block devices enumerate successfully
- no `/metadata` mount
- no `/data` mount
- no `init second stage started`
- first-stage `/init` aborts through `InitFatalReboot -> FirstStageMain`
- system reboots to bootloader around 6.3s

`DATA_MOUNT=0 META_MOUNT=0 SECOND=0 ZSIG=0`.

## Consequence
The next causal boundary is not userdata formatting, data seeding, zygote, graphics, or framework. It is first-stage partition discovery/mounting. Do not run another seed/filesystem/zygote matrix until first-stage can resolve and mount its required `first_stage_mount` entries (especially metadata and the system/vendor logical/block mapping).

The explicit boot-device property alone did not fix this boundary, so the next test should inspect/reproduce Android emulator block topology and by-name symlink creation rather than vary `/data` contents.
