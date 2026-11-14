# TikTok LIVE Studio - isolated Windows cloud compatibility check
DATE: 2026-11-11
STATUS: BLOCKED_BY_HOST_CAPABILITY
AREA: tiktok-live-native-cloud-windows
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43027322351
JOB: 130545195052

## Observed in actual GitHub-hosted Windows instance
- Windows Server 2025 Datacenter, 16 GiB RAM, interactive session id 2 with explorer.exe and 1024x768 visible remote session.
- One video controller, classified VIRTUAL_OR_BASIC; no vendor-accelerated GPU (NVIDIA/AMD) detected.
- Host virtualized; no dedicated GPU to satisfy practical TikTok LIVE Studio hardware requirements or reliable sustained video render/encode.
- Compatibility gate returned TIKTOK_NATIVE_STUDIO_CLOUD_HOST_GATE=UNSUITABLE. The official LIVE Studio was deliberately not installed or authenticated on an inadequate, disposable host.

## Prior independent eligibility check
- TikTok Studio and LIVE Center rendered from the existing Lucas4 browser state but exposed no button for browser Go LIVE or virtual camera. Seller Center redirected to account registration: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43026499727.
- A fake cloud camera and microphone did work in Chromium, but there was no eligible TikTok browser LIVE entrypoint to receive them.

## User-computer isolation requirement
- Run graphical tests only on cloud-hosted workers, separate browser automation contexts, or independent virtual desktops explicitly isolated from the owner's interactive session.
- NEVER move the main pointer, send foreground keys, take focus, launch visible browser windows, or play audio on the owner's desktop.
- Use API/DOM or control-bound automation in the separate runtime; default to no UI. If separate GUI cannot operate without foreground focus, do not perform it on the owner's PC.

## Disposition
- No native TikTok LIVE completed with the current Windows cloud host; activation would need a suitable persistent graphical Windows environment with GPU and official account eligibility.
- Existing Hostinger/Restream six-hour TikTok transmitter stays enabled and separate from Kwai. Changing transport to a simulated native app must not be claimed to override eligibility or content rules.
- No additional paid GPU VM has been provisioned. Current native-host approach is closed pending new compatible infrastructure.