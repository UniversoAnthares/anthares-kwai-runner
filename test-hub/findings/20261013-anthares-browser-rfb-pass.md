# 2026-10-13 — Anthares-browser authenticated noVNC/RFB handshake PROVEN

## Failure resolved
The hosted browser gateway was authenticating the public noVNC WebSocket correctly but timing out before receiving the RFB greeting from x11vnc through local websockify.

The runtime now caps `RLIMIT_NOFILE` to 65536 before x11vnc starts. This avoids pathological descriptor-table scanning inside LibVNCServer on hosted containers with extremely large inherited limits.

## Practical proof
Render service `srv-db6onc7f3r2c73btqcr0`, deploy carrying commit `0de421991016a7afb1385763635ab1d791e189c0`, emitted the following real end-to-end sequence on 2026-10-13:

- control API ready
- isolated Xvfb started
- VNC loopback listener ready
- loopback-only noVNC websocket proxy started
- Chromium started
- `ws auth cookie_present=True valid=True origin_valid=True`
- FastAPI accepted `WebSocket /novnc/websockify`
- gateway reported `local websockify connected`
- final result: `authenticated noVNC websocket-to-RFB handshake PASS`

This proves the server-side chain:

`signed Anthares noVNC session -> FastAPI authenticated WebSocket -> loopback websockify -> x11vnc/RFB`

It does not by itself prove a human-visible Kwai login session. Authentication to the target service remains a separate gate.

## Related CI correction
The isolation contract was updated to accept the explicit IPv4 loopback target `127.0.0.1:6080 127.0.0.1:5900`; the previous assertion expected `localhost` and was stale after the security-oriented IPv4 loopback change.
