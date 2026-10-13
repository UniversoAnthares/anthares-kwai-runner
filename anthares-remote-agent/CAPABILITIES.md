# Anthares Remote Agent — capability contracts

Version: 0.3

All operations are submitted as a job with `id`, `type`, `args` (`map[string]string`) and optional `timeout_seconds`. Normal synchronous timeout is 30 seconds and is capped at 120 seconds. Results contain `id`, `ok`, `output` or `error`, `started_at`, and `ended_at`.

## Core and diagnostics

| type | args | output | authorization / limits |
|---|---|---|---|
| `ping` | none | `pong` | authenticated device channel |
| `system_info` | none | JSON OS/CPU/RAM/GPU/disks/boot/agent version | read-only |
| `safe_environment` | none | allowlisted non-secret environment values | read-only |
| `network_info` | none | interfaces, addresses, gateways and DNS | read-only |
| `tcp_connections` | none | up to 2000 TCP connection rows | read-only |
| `scheduled_tasks` | none | up to 2000 scheduled tasks | read-only |
| `event_log` | `name`,`max` | metadata for up to 200 events | defaults to System/Application; other logs require `ANTHARES_ALLOWED_EVENT_LOGS` |
| `process_list` | none | tasklist CSV | read-only |
| `process_info` | `pid` | process metadata without command line | read-only |
| `service_list` | none | service inventory | read-only |

## Shell

`type=shell`

Args: `command` required; `shell` = `powershell` (default) or `cmd`.

Requires `ANTHARES_ALLOW_SHELL=1`. Output on success is JSON `{stdout,stderr,exit_code,timed_out}`. Stdout and stderr are independently limited to 512 KiB. The job-level timeout is 30 seconds by default and 120 seconds maximum. A non-zero exit returns `ok=false`; the structured command result remains available as the operation output produced by the shell helper.

## Files

Every file operation requires `ANTHARES_ALLOWED_ROOTS` and passes root-containment validation. Existing symbolic-link/reparse-like path components are rejected. Authorized roots themselves cannot be recursively deleted.

| type | args | output / limit |
|---|---|---|
| `file_stat` | `path` | metadata JSON |
| `file_list` | `path` | JSON, max 1000 entries |
| `file_acl` | `path` | Windows owner/ACL JSON |
| `file_read` | `path` | base64, max 1 MiB |
| `file_write` | `path`,`base64` | atomic write, max 1 MiB |
| `file_read_chunk` | `path`,`offset`,`length` | JSON + base64, chunk max 512 KiB |
| `file_write_chunk` | `path`,`offset`,`base64`,`truncate` | chunk max 512 KiB |
| `file_mkdir` | `path` | resulting path |
| `file_remove` | `path`,`recursive` | removed path |
| `file_rename` | `src`,`dst` | destination path |
| `file_copy` | `src`,`dst` | destination path, temp-file + rename |
| `file_sha256` | `path` | lowercase SHA-256 hex |
| `file_write_atomic` | `path`,`base64` | atomic write, max 8 MiB |

## Clipboard

| type | args | output |
|---|---|---|
| `clipboard_get` | none | plaintext clipboard |
| `clipboard_set` | `text` | command output |

Clipboard content must never be logged by the MCP layer. These operations require an interactive Windows session.

## Screenshot

`type=screenshot`; optional `display` is a zero-based monitor index or `all`. Output is JPEG base64. Requires an interactive Windows session. The MCP layer must request screenshots explicitly and must not publish returned images to public CI artifacts.

## Processes

`process_start`: args `path`, optional `args_json`. `args_json` is a JSON array of strings, limited to 64 arguments and 32 KiB total argument data. The executable path must exactly match one entry in `ANTHARES_ALLOWED_EXECUTABLES` (semicolon-separated absolute paths). Shell-style argument strings are rejected; decoded arguments are passed directly to the executable without invoking `cmd.exe`.

`process_kill`: arg `pid`. The agent resolves the executable path of the PID and permits termination only when it exactly matches `ANTHARES_ALLOWED_EXECUTABLES`. System PIDs 0–4 are always rejected.

`process_list` and `process_info` remain read-only and do not require the process allowlist.

## Windows services

`service_list` and `service_status` are read-only.

`service_start` / `service_stop`: arg `name`. Mutating operations require an exact case-insensitive match in `ANTHARES_ALLOWED_SERVICES` (semicolon-separated service names).

## Persistent jobs

`job_start`: args `command`, optional `name`; requires `ANTHARES_ALLOW_SHELL=1`; returns a 16-hex-character `job_id`.

`job_list`: optional `limit` (max 100), `include_command`.

`job_status`: `job_id`, optional `include_command`.

`job_logs`: `job_id`, optional `offset_bytes`, `max_bytes` (max 256 KiB), `tail_lines`.

`job_cancel`: `job_id`; terminates the stored process tree.

Long jobs use a separate hidden PowerShell process and persisted metadata under `%PROGRAMDATA%\\AntharesRemoteAgent\\jobs`, so status/log discovery survives restart of the Anthares Remote Agent process while the underlying Windows process remains alive.

## Concurrency and delivery

The polling loop accepts multiple jobs concurrently. `ANTHARES_MAX_CONCURRENT` defaults to 4 and accepts values 1–8. Result delivery is retried up to five times with exponential delays. The agent channel requires HTTPS plus bearer/device authentication.

## Validation model

The implementation is intentionally testable without AI Commander, MeshCentral, WinRemote or another pre-existing remote-control agent. CI uses native GitHub-hosted Windows runners for compile, vet, filesystem lifecycle and Windows runtime probes. Clipboard and screenshot probes are executed when the hosted Windows session exposes an interactive clipboard/desktop; otherwise those two probes are explicitly skipped because the GitHub runner itself has no interactive desktop.

## MCP mapping guidance

The MCP integration should expose one typed tool per capability rather than a generic unrestricted dispatcher. Mutating tools must preserve the agent's allowlists and must not add bypass parameters. Sensitive outputs (clipboard, screenshots, command output) should only be returned to the requesting authorized conversation and should not be copied into public logs.
