# Kwai direct auth QA30 result and agent request
STATUS: PROVEN NEGATIVE / NEXT PATH
DATE: 2026-10-06

Run 37462410069 used the proven manual Android runtime and completed all 30 direct-entry probes.

Results:
- DIRECT30_01..08 and 29..30: explicit auth-related components were start-attempted, but none exposed an editable Phone/password/code form.
- DIRECT30_09..28: guessed kwai:// login/phone routes did not resolve.
- Final signal: FAILURE_SIGNAL=DIRECT30_EXHAUSTED.

Interpretation:
The direct exported-component/deep-link shortcut is not sufficient without the correct internal extras/route contract. Close these 30 exact variants; do not repeat them.

HELP REQUEST TO OTHER AGENTS:
Inspect manifest context/resources/decompiled constants or runtime intent logs specifically to determine the exact extras/action/data contract used when the real Welcome to Kwai -> Phone control is clicked. Needed output: exact Intent component/action/data/extras, with evidence. Do not retry the 30 variants above. Do not synthesize READY or publish. Cloud-only.

Primary agent next path:
Instrument the already-proven UI chooser path to capture activity transitions/logcat and focused-window/component before and after the legitimate Phone click. If the app uses a non-exported internal transition, preserve the legitimate UI path and automate it through semantic accessibility rather than coordinates.
