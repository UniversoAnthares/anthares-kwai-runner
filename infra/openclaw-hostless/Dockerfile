# Official image, pinned to the 2026-09 extended-stable line.
# Validation only: the Hostless free app does not have a persistent SQLite volume.
FROM ghcr.io/openclaw/openclaw:2026.9.36-slim

ENV HOME=/tmp/anthares-openclaw-home \
    OPENCLAW_STATE_DIR=/tmp/anthares-openclaw-home/.openclaw \
    OPENCLAW_CONFIG_DIR=/tmp/anthares-openclaw-home/.openclaw \
    NODE_OPTIONS=--max-old-space-size=640

EXPOSE 18789

# Fail closed: a token is mandatory, and no account/connector credentials are provisioned.
# Exec forwards container termination directly to the OpenClaw Gateway process.
CMD ["/bin/sh", "-ec", "test -n \"\u0024{OPENCLAW_GATEWAY_TOKEN:-}\" || { echo OPENCLAW_GATEWAY_TOKEN_REQUIRED >&2; exit 78; }; mkdir -p \"\u0024OPENCLAW_STATE_DIR\" \"\u0024OPENCLAW_CONFIG_DIR\"; exec node dist/index.js gateway run --bind lan --auth token --port \"\u0024{PORT:-18789}\" --allow-unconfigured"]
