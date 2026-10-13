# Anthares Remote MCP v2

Canonical ChatGPT-facing endpoint:

`https://anthares-remote-mcp-v2.onrender.com/mcp`

## Architecture

ChatGPT -> OAuth 2.1/PKCE gateway -> Streamable HTTP MCP -> Ed25519-signed control bridge -> Anthares Remote Agent -> DESKTOP-FTDK0HP.

The Windows device initiates outbound polling to the control plane. No inbound port is exposed on the PC.

## Authentication

- ChatGPT-facing authorization uses OAuth 2.1 authorization-code + PKCE S256 and refresh tokens.
- OAuth authorization is approved with a one-time code delivered directly to the registered Windows clipboard through ARA.
- MCP-to-control authentication uses Ed25519 request signatures with a 30-second freshness window and replay rejection.
- The new path does not use `ARA_SHARED` and does not require `ARA_OAUTH_ADMIN_PASSWORD`.
- Read and write MCP operations are separated by `ara.read` and `ara.write` scopes.

## Tools

The signed remote MCP exposes exactly 30 tools covering status, system information, shell execution, processes, services, clipboard, screenshots, allowlisted file operations, hashes, atomic writes and detached jobs.

## Verified execution

A live OAuth authorization request completed the signed `clipboard_set` operation on `DESKTOP-FTDK0HP` before the authorization form was rendered. This proves the production path MCP v2 -> Ed25519 control bridge -> ARA -> Windows without AI Commander and without the legacy shared controller secret.

The control service uses a threaded Gunicorn worker so long-polling MCP execution can coexist with device heartbeat, job polling and result upload.

The temporary recovery bootstrap has been disabled again and returns HTTP 401 without authorization.

## Deployment

Canonical Render service: `anthares-remote-mcp-v2` (`srv-db6o0d5g1s2s738s7bp0`).
Redundant Render service: `anthares-remote-mcp` (`srv-db6naljbc2fs739og1s0`).

Both public `/health` endpoints were independently checked and returned HTTP 200 with `oauth=configured`, `control=signed-ready`, and `mcp=ready`. Both OAuth protected-resource metadata endpoints returned HTTP 200. The redundant deployment `dep-db6o79mk1f9s73asgcb0` reached `live`.

These health checks prove availability of both signed bridges, not ChatGPT account registration or successful native MCP tool execution.
Control service: `anthares-remote-control` (`srv-db6mj8navr4c73cqvgo0`).

The public `/health` endpoint is healthy only when OAuth, the internal MCP and the signed control bridge are all ready.

## Completion criterion

The backend is ready. The project remains incomplete until ChatGPT itself registers the custom MCP endpoint, completes OAuth, discovers the tools and executes a real ARA tool call. That product-level registration is intentionally tracked separately from the backend deployment proof.
