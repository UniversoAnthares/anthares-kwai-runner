# Anthares Remote MCP

Canonical ChatGPT-facing endpoint:

`https://anthares-ara-mcp.anthares1.workers.dev/mcp`

## Architecture

ChatGPT -> OAuth/PKCE Cloudflare gateway -> signed Cloudflare control -> Anthares Remote Agent -> `DESKTOP-FTDK0HP`.

The Windows device initiates outbound traffic. No inbound port is exposed on the PC.

## Authentication

- ChatGPT-facing authorization uses OAuth authorization-code + PKCE and refresh tokens.
- MCP-to-control requests are signed and replay protected.
- Device execution uses the ARA device identity/credential.
- Render is not part of the canonical authentication or state path.

## State and redundancy

- MCP/OAuth state: Cloudflare Durable Object.
- Control state: Cloudflare Durable Objects/SQLite.
- External PostgreSQL redundancy: Neon project `anthares-ara-ha`.
- Container/Chromium compute: Northflank where required.
- GitHub/GitLab issue queues remain independent recovery transports.
- Render services `anthares-remote-mcp*` remain legacy emergency fallbacks only and may disappear when the free quota expires.

## Completion proof

The Cloudflare MCP app has already been connected to ChatGPT and a real `remote_exec` call completed successfully. The canonical endpoint therefore does not require either Render MCP gateway.

## Permanent rule

Do not introduce an `onrender.com` endpoint as a default, primary authority, unique signing-key source or required runtime dependency. Render may only be referenced explicitly as final emergency fallback during the retirement window.
