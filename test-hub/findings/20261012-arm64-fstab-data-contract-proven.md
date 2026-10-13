# Android 30 ARM64 /data contract recovered from vendor fstab
STATUS: PROVEN
AREA: kwai-arm64-runtime
DATE: 2026-10-12
PIPELINE: https://gitlab.com/universo-anthares-group/anthares-kwai-runner/-/pipelines/2940628590
JOB: 17126931353

## Decisive evidence
The packaged `vendor.img` is a raw GPT disk. Its `vendor` partition starts at sector 2048, is 47 MiB, and contains an ext4 filesystem. `/etc/fstab.ranchu` was extracted directly from that partition.

Relevant contract:

`/dev/block/vdc /data ext4 noatime,nosuid,nodev,nomblk_io_submit,errors=panic wait,check,quota,fileencryption=aes-256-xts:aes-256-cts,reservedsize=128M,fsverity,keydirectory=/metadata/vold/metadata_encryption`

Metadata contract:

`/dev/block/platform/a003c00.virtio_mmio/by-name/metadata /metadata ext4 noatime,nosuid,nodev wait,formattable,first_stage_mount`

Signal: `ARM64_FSTAB_FORENSICS=PASS`.

## Consequences
1. `/data` must be an ext4 block device at `vdc`; the 1 MiB packaged `userdata.img` is not a ready filesystem and cannot satisfy this contract.
2. Any hand-built QEMU topology must preserve the virtio block-device ordering expected by `fstab.ranchu`; merely attaching a userdata image somewhere in the device list is insufficient.
3. A replacement test must create a sufficiently large ext4 userdata disk (greater than the 128 MiB reserved size), attach it as the third virtio block device so it enumerates as `vdc`, and keep metadata exposed through the named metadata partition/path expected by first-stage mount.

Do not continue interpreting seed/repair failures from the old known-good-data matrix as zygote hypotheses until this device/filesystem contract is satisfied.
