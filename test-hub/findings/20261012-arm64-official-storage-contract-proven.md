# Android 30 ARM64 official emulator storage contract recovered
STATUS: PROVEN
AREA: kwai-arm64-runtime
DATE: 2026-10-12
GITLAB_PIPELINE: https://gitlab.com/universo-anthares-group/anthares-kwai-runner/-/pipelines/2940650418
GITLAB_JOB: 17127066553

## Package evidence
Fresh inspection of `system-images;android-30;default;arm64-v8a` proves:
- `system.img`: GPT with `vbmeta` + `super`;
- `encryptionkey.img`: GPT with a `metadata` partition;
- `vendor.img`: GPT with a `vendor` partition;
- packaged `userdata.img`: 1 MiB seed/placeholder, not a ready filesystem.

Signal: `ARM64_OFFICIAL_DISK_CONTRACT=PASS`.

## AOSP emulator contract
For ARM64 this image family uses emulator disk roles in logical CLI order:
`[sdcard], vendor, encryption_key, userdata, cache, system`.

ARM guest block enumeration reverses that order. With no sdcard, expected block names are:
- system -> vda
- cache -> vdb
- userdata -> vdc
- encryption_key / metadata -> vdd
- vendor -> vde

The dynamic-partition boot device is derived from the system disk. For this five-disk ARM64 arrangement the expected system transport is `a003600.virtio_mmio`; `a003c00.virtio_mmio` belongs to the encryption/metadata disk and must not be used as the system `androidboot.boot_devices` value.

## Consequence
All earlier custom QEMU matrices using vendor=vda/system=vdb and/or `androidboot.boot_devices=a003c00.virtio_mmio` are superseded for first-stage partition discovery. The next valid boot must reproduce this official disk-role order, use the packaged `encryptionkey.img`, provide a real ext4 userdata at vdc, and expose the ranchu fstab to first-stage init.
