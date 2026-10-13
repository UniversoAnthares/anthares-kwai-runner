# Anthares Remote MCP v2

Canonical ChatGPT-facing endpoint:

`https://anthares-remote-mcp-v2.onrender.com/mcp`

## Architecture

ChatGPT -> OAuth 2.1/PKCE gateway -> Streamable HTTP MCP -> Ed25519-signed control bridge -> Anthares Remote Agent -> DESKTOP-FTDK0HP.

The Windows device initiates outbound polling to the control plane. No inbound port is exposed on the PC.

## Authentication

- ChatGPT-facing authorization uses OAuth 2.1 authorization-code + PKCE S256 and refresh tokens.
- OAuth authorization is approved with a one-time code delivered directly to the registered Windows clipboard through ARA.
- MCP-to-control authentication uses short-lived Ed25519 request signatures with a 30-second freshness window and replay rejection.
- The new path does not use `ARA_SHARED` and does not require `ARA_OAUTH_ADMIN_PASSWORD`.
- Read and write MCP operations are separated by `ara.read` and `ara.write` scopes.

## Tools

The signed remote MCP exposes exactly 30 tools covering status, system information, shell execution, processes, services, clipboard, screenshots, allowlisted file operations, hashes, atomic writes and detached jobs.

## Deployment

Canonical Render service: `anthares-remote-mcp-v2` (`srv-db6o0d5g1s2s738s7bp0`).
Control service: `anthares-remote-control` (`srv-db6mj8navr4c73cqvgo0`).

The public `/health` endpoint is healthy only when OAuth, the internal MCP and the signed control bridge are all ready.
