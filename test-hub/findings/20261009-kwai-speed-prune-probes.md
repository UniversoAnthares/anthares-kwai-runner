# Kwai speed prune probes after slim v4
STATUS: PROVEN
AREA: kwai-speed
DATE: 2026-10-09
RUNS: 37932201397; 37932318913; 37932710311; 37933169195
SUPERSEDES: none

## API/system image alternatives
API30 Google APIs download probe: 1,438,186,618 bytes versus API35 Google APIs 1,738,815,903 bytes (~17% smaller), insufficient alone to reach the desired total-time reduction. AOSP ATD API30 was tested without creating a cache: install 20 s, installed image 3,349,537,028 bytes, cold boot 25 s. Not promoted.

## AVD QCOW necessity
Run 37932710311 restored proven slim AVD v4 and tested removal of large QCOW disks independently. Removing userdata-qemu.img.qcow2 made kwai-ready fail and fall back to cold boot (36 s). Removing cache.img.qcow2 likewise failed real snapshot load and cold-booted (32 s). Both disks are causally required; do not prune them.

## QCOW structure
userdata-qemu.img.qcow2 has backing userdata-qemu.img and internal snapshots kwai-ready + default_boot. cache.img.qcow2 and encryptionkey.img.qcow2 also contain both internal snapshot tags. External snapshots/default_boot was already removed in v4, but internal default_boot tags remain candidates for a safe qemu-img snapshot deletion probe.

## System image prune
Run 37933169195: API35 Google APIs raw system-image directory 3,754,692,685 bytes. Dominated by system.img 3,576,692,736 and vendor.img 116,391,936. Removing NOTICE.txt saves 20,115,976 bytes and still loads kwai-ready in 4 s (2,324 ms snapshot load). Removing data/ saves only another 63,185 bytes and still loads in 4 s (2,292 ms). Savings are too small to justify a replacement cache; preserve existing system image cache v1.

## Conclusion
Preserve slim AVD v4 + API35 image v1 + emulator v1 as current proven baseline. Do not promote API30 ATD, QCOW removal, or system-image NOTICE/data cache variants. Next valid experiment: delete only internal qemu snapshot tag default_boot from QCOWs, then validate kwai-ready and measure actual compressed cache potential before any save.

## Coordination
Only kwai-speed isolated workflows/findings touched. Login agent unchanged. No user PC used.
