# Kwai 15-way QA expansion after login surface proof
STATUS: PROVEN
AREA: kwai-login / ready-gate / promotion-gate
DATE: 2026-10-06

## Runtime
Run 37452048266: SUCCESS.
Proved EMULATOR_BOOTED -> APPS_INSTALLED -> FSM_MAIN_REACHED -> LOGIN_CONTROL_VISIBLE=1 -> LOGIN_SURFACE_REACHED.
The real chooser exposed Welcome to Kwai / Continue with Google / Facebook / Phone.

## Front 1: semantic login selector — 15/15
Run 37452895974: SUCCESS.
Signal: KWAI_LOGIN_SELECTOR_QA15_OK=15.
Covered text/content-desc/case/spacing/localization/merged-tree positives plus negative controls and Profile fallback distinction.

## Front 2: Studio observation — 15/15 observations completed
Run 37452048266.
All STUDIO15_01..15 remained in Chrome first-run UI; no phone/code form. Classify Studio web route as non-evidence for app authentication. It is non-blocking.

## Front 3: READY proof gate — 15/15
Run 37453018607: SUCCESS.
Signal: KWAI_READY_GATE_QA15_OK=15.
Valid/fail-closed cases include missing/invalid JSON/not-ready/incomplete/bad time/stale/future/account mismatch/custom age/numeric time/extra fields.

## Front 4: promotion contract — 15-case matrix
Run 37453156495: SUCCESS.
Covers missing queue/generation/source/window, invalid generations and time windows, and valid large generation/fractional window.

## Current boundary
Authentication surface is real and deterministic. No authenticated READY proof exists yet. Publication remains correctly fenced behind READY + promotion contract.
