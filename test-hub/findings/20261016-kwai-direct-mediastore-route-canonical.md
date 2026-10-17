# Kwai physical publication route — canonical direct MediaStore path
STATUS: PROVEN
DATE: 2026-10-16
AREA: kwai-physical-publisher

DECISION: The legacy `us.anthares.agent.redmi` / `anthares-kwai://send` route is retired and must never be used again. It was removed from the device and from the runtime bridge. The old confirmation dialog “Abrir vídeo no Kwai?” is not part of the canonical flow.

CANONICAL_INGRESS: Download the approved HTTPS media, verify SHA-256 on Windows, stage it under Android `Movies/Anthares`, rescan into MediaStore, resolve the resulting `content://media/external/video/media/<id>` URI, then launch `android.intent.action.SEND` with MIME `video/mp4` directly to package `kwai.lite.video`.

RUNTIME_PROOF: A direct ACTION_SEND using MediaStore URI `content://media/external/video/media/1000264493` launched `kwai.lite.video/com.yxcorp.gifshow.v3.EditorActivity` successfully on the physical device.

POST_SELECTION_FLOW: After the video is selected/opened in the Kwai editor, there are only two publication steps. Screen 1: click `Próximo` immediately; do not inspect or change any other option. Screen 2: click `Publicar` immediately; do not inspect or change caption, privacy, location, duets, advanced settings, cover, or any other field unless a future explicit requirement changes this rule.

INVARIANT: No legacy Anthares confirmation dialog, no deep-link handoff, no alternate Kwai package, and no additional validation delay between these two UI steps. `kwai.lite.video` is the fixed target for this physical-phone route.
