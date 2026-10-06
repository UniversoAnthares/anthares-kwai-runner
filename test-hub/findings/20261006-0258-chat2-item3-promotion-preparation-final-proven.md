# CHAT 2 item 3 — real-publish promotion preparation closed
STATUS: PROVEN
AREA: kwai-publish
DATE: 2026-10-06
RUN: 37406149502
COMMIT: 84ba3a18d6b60bb2d14506c83c191125755d2d2c
SUPERSEDES: test-hub/findings/20261006-0248-kwai-real-publish-promotion-readiness-contract.md

The production workflow now wires an executable fail-closed promotion contract through kwai_real_publish_promotion_gate.py. It requires canonical queue job identity, lease generation, source identity and valid source interval. The production workflow remains intentionally guarded and does not invoke kwai_publish.sh before independent kwai-login reports READY.

The continuously executable readiness proof verifies:
- explicit AUTH READY gate;
- production remains guarded;
- executable canonical contract is wired;
- job ID + lease generation + source interval are mandatory/fail-closed;
- publisher fencing/heartbeat/started-before-commit remains present;
- post-start failure retains UNCERTAIN handling.

CHAT 2 promotion-preparation work is complete. The only remaining transition is externally triggered: independent kwai-login/session READY, followed by the separately scoped one-job real canary and activation decision.
