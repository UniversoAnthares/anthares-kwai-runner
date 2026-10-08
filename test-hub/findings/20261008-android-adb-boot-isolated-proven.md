# Android/ADB isolated boot confirmed
STATUS: PROVEN
AREA: android
DATE: 2026-10-08
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/workflows/android-adb-boot-isolated.yml
JOB: user reported passing run; exact successful run/job ID not yet independently retrieved
COMMIT: 7ffe4cafbeb4ce01e33877e10dcf796d36e2cacf
SUPERSEDES: test-hub/findings/20261008-android-boot-isolated-lease.md

## Objective
Validate GitHub hosted Android API35 x86_64 emulator and ADB independently from Kwai login/publishing.

## Result
User confirmed the new isolated workflow passed after the POSIX-shell fix and self-trigger on main. Prior failed run 37830293589 independently showed emulator boot completed, ADB usable and sys.boot_completed=1, but script failed on /bin/sh pipefail; corrected in commit ac86ca6c82bf2ba92c871f34efd350fcea83daef. New workflow trigger committed in 7ffe4cafbeb4ce01e33877e10dcf796d36e2cacf.

## Evidence boundary
Reported PASS is user confirmation; successful run ID and decisive marker ANDROID_ADB_BOOT=PROVEN remain to be independently retrieved. Do not infer Kwai authentication, session persistence or publication from this isolated diagnostic.

## Consequence
Do not repeat the boot-only failure path. Move to independent Kwai auth/publish validation only after checking active leases; preserve publisher quarantine and verification gates.
