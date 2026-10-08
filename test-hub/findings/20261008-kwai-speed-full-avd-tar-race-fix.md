# Full AVD archive race after successful local snapshot
STATUS: PARTIAL
AREA: kwai-speed
DATE: 2026-10-08
RUN: 37861198690
JOB: 113597062173
COMMIT: ed7136059a63b1bd10ee3e2913206d1a6d30d869
SUPERSEDES: 20261008-kwai-speed-cross-run-fallback-and-full-avd-fix.md

## OBSERVED
Run conclusion FAILURE. Android image, emulator, vault cache hits. New full AVD cache key kwai-speed-avd-fullstate-android35-v2 miss expected on first build. PREP_TOTAL_SECONDS=0; COLD_BOOT_SECONDS=27; TOTAL_SECONDS=67. Same-run snapshot save 8 seconds, restore boot 3 seconds. Packaging full AVD failed: tar: avd/kwai-speed.avd/userdata-qemu.img.qcow2: file changed as we read it. Thus no full AVD cache saved; cross-run test NO_ARCHIVE.

## ROOT CAUSE
Emulator still writing to AVD disk when tar read full AVD. Previous snapshot-only archive did not include mutable disk file.

## FIX
Commit 9c8c7f8c19b5a2a908a97767baba4a991af2bd88 sends adb emu kill, waits for qemu process exit, syncs filesystem before tar. New workflow push run should save full AVD cache. Follow-up independent run needed to validate actual snapshot load, not cold boot fallback.

## COORDINATION
Only isolated benchmark workflow and speed findings edited. No changes to kwai-login files, no local PC.
