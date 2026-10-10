# Anthares Control Plane v1
Original cloud-first replacement for repeated manual recovery loops.

Four evidence-gated stages: verified remote identity, authenticated persistent
session, real publication proof, and unattended runner. A stage never advances
without verified evidence and successful upstream stages.

Runs for free on GitHub Actions public-repository infrastructure, subject to
platform limits. Does not depend on the user's PC for cloud validation.

This implementation is the **state and QA core**, not yet a working publisher.
No login tokens, browser profiles, cookies, credentials, or private sessions
belong in this repository, CI logs, or artifacts. Session transfer must use
an authorized secure channel; do not bypass authentication challenges.

Run: `python -m unittest discover -s control_plane`
Inspect: `python control_plane/engine.py` (exit 2 means unverified).
