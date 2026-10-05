# Exported Kwai UriRouterActivity accepts direct video ACTION_SEND
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388030409
JOB: 112026171392
COMMIT: d9a144b23fbca831e4b382aa710549b68d9af77a
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-1927-qa-kwai-publish-safety-static-proven.md; current gallery selection still taps candidates[0].
FAILED_AVOIDED: no publication and no runtime SEND probe was launched under the active kwai-publish lease; this uses the already-valid manifest artifact from run 37388030409.
SUCCESS_SIGNAL: valid Manifest declares an exported enabled Kwai activity accepting android.intent.action.SEND with MIME video/*.
FAILURE_SIGNAL: SEND filter belongs only to a disabled/non-exported component or does not accept video/*.
TEST_VALIDITY: run 37388030409 already proved aapt validity and uploaded manifest-tree.txt; this finding is static contract evidence, not runtime acceptance.

## Resultado
The valid Manifest artifact shows `com.kscorp.oversea.platform.router.ui.UriRouterActivity` with `android:exported=true`. Inside that same activity, an intent-filter accepts `android.intent.action.SEND` + `android.intent.category.DEFAULT` + `android:mimeType=video/*`; a second filter accepts SEND_MULTIPLE + video/*. This is materially stronger than the current gallery heuristic because Android can hand a specific content URI directly to the Kwai router.

## Consequência
After the current kwai-publish lease is free, test direct single-video ACTION_SEND as the preferred deterministic media-ingress candidate. The probe must use exactly one MediaStore content URI, grant read permission, verify the foreground/UI transition, and stop before any Publish action. Success means the composer/editor demonstrably contains the intended imported media without tapping an arbitrary gallery tile. Failure must preserve the existing MediaStore path until another causal alternative is proven.
