# Android ARM64 SDK userdata.img is a placeholder, not a ready /data filesystem
STATUS: PROVEN
AREA: kwai-arm64-runtime
DATE: 2026-10-12
PIPELINE: https://gitlab.com/universo-anthares-group/anthares-kwai-runner/-/pipelines/2940620710
JOB: 17126882343

## Decisive evidence
Independent GitLab forensic inspection installed `system-images;android-30;default;arm64-v8a` and inspected the packaged `userdata.img` without booting an emulator.

Observed:
- size: exactly 1,048,576 bytes (1 MiB);
- `file`: `data`;
- `blkid`: no filesystem;
- `dumpe2fs`, `tune2fs`, `e2fsck`, and `debugfs`: invalid/bad superblock;
- no usable filesystem or data directories exist in the packaged image;
- neighboring package files include `system.img` (~3.23 GB), `vendor.img` (~51 MB), `ramdisk.img`, and `encryptionkey.img`.

Signal: `ARM64_USERDATA_FORENSICS_EXTERNAL=PASS`.

## Consequence
The packaged SDK `userdata.img` must not be treated as a known-good mounted `/data` image. Any matrix that copies it and then attempts ext4 mount/repair/seed operations is testing a placeholder and will classify those preparation variants incorrectly.

The next causal step is to inspect the ramdisk fstab for the exact `/data` block device/filesystem/flags, then create a correctly sized/formatted userdata disk (or reproduce the Android emulator's userdata initialization) before testing zygote/data behavior.
