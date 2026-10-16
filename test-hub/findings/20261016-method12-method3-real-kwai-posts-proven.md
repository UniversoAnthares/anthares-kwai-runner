# CORTES — method 1+2 and method 3 real Kwai publication proof
STATUS: PROVEN
AREA: kwai-publish|anthares-android-runtime|cortes
DATE: 2026-10-16
TARGET_ACCOUNT: lucasrosalem

## Result
Two distinct real Kwai posts were published from the already-proven CORTES masters through the canonical MEmu fallback selected by Anthares Android Runtime.

### Method 1+2
- source master SHA-256: `cd3d23c0fe083575c620a276500335de0fec1d9a615a164a7b0b8c931b18ec28`
- Android MediaStore name: `anthares_method12_cd3d23c0.mp4`
- job: `method12-real-memu-20261016-cd3d23c0`
- caption: `Anthares teste metodo 1+2 20261016`
- agent signals: `LOCAL_HANDOFF=VERIFIED`, `AUTO_PUBLISH=ADVANCE`, `AUTO_PUBLISH=CAPTION_SET`, `AUTO_PUBLISH=PUBLISH_CLICKED`, `AUTO_PUBLISH=CONFIRMED`
- **verified public link:** `https://k.kwai.com/p/nC4nlVCT`
- round-trip proof: the link was copied only after deterministic navigation to the own profile (`id_home_bottom_tab_me`), opening the post stream, moving specifically to the item whose visible author/caption were `Lucas Rosalem` + `Anthares teste metodo 1+2 20261016`, then reopening the copied short link. The reopened detail screen again exposed the same author and exact caption.
- **invalidated former association:** `https://k.kwai.com/p/FN0BWCRJ` was previously reported as the method-1+2 link, but user-side verification showed it belongs to `Plantão do Amostradinho`. The publication proof itself was valid; that URL association was not. It must not be reused as evidence.

### Method 3
- source master SHA-256: `4ce5276f27484e0e50bebcf06653b9bf021ea655c0888f29fc9f050c3ea8b1d3`
- Android MediaStore name: `anthares_method3_4ce5276f.mp4`
- job: `method3-real-memu-20261016-4ce5276f`
- caption: `Anthares teste metodo 3 20261016`
- agent signals: `LOCAL_HANDOFF=VERIFIED`, `AUTO_PUBLISH=ADVANCE`, `AUTO_PUBLISH=CAPTION_SET`, `AUTO_PUBLISH=PUBLISH_CLICKED`, `AUTO_PUBLISH=CONFIRMED`
- public link recovered from the Kwai share sheet: `https://k.kwai.com/p/QFrQCrAh`

## Positive account/post verification
The profile/post stream exposed both exact captions under `Lucas Rosalem` / `lucasrosalem`:
- `Anthares teste metodo 3 20261016` — 2026-10-16 12:56 PM
- `Anthares teste metodo 1+2 20261016` — 2026-10-16 12:54 PM

For method 1+2, the corrected proof additionally includes a full short-link round trip back into Kwai detail view, where `Lucas Rosalem` and the exact test caption were both visible.

## Content-quality limitation discovered after publication
The original method-1+2 canary validated authenticated bounded acquisition, media processing and real publication, but **did not validate the intended semantic CORTES algorithm**. Its old method 2 only normalized/cropped the fixed 8–98 second interval. It therefore bypassed the canonical transcript-driven selector and mandatory semantic microcuts used by CORTES production. This is why the published test is only an intro-like fragment and contains no meaningful microcuts. Do not cite that post as proof of semantic selection or filler/repetition removal.

## Anthares ADB / Runtime robustness proof
The canonical policy remained `physical_android -> memu_android`; physical transport was unavailable, so Runtime selected `memu_android`. During this session the MEmu ADB transport was lost and Runtime recorded successful recovery. Where the ADB socket itself remained unstable, the same guest was also controlled through the MEmu guest-command channel; no Windows reboot/shutdown/logoff was used.

This proves the publication mechanics: executor selection -> verified media handoff -> real publish -> positive confirmation -> own-profile verification -> public URL round trip. Semantic selection/microcuts are a separate acceptance gate and must be proven independently.

## Android Agent changes used by the proof
The agent supports Android SDK 25 MEmu, an AccessibilityService semantic bridge independent of broken `uiautomator`, verified local MediaStore handoff by SHA-256, full/lite Kwai package observation, deterministic resource-id navigation, and an ADB/guest-command receiver for semantic snapshots/clicks/clipboard evidence. Automatic routing policy was not changed.
