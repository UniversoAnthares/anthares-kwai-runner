# Anthares Remote Agent — capability contracts

Version: 0.3 draft

All operations are submitted as a job with `id`, `type`, `args` (`map[string]string`) and optional `timeout_seconds`. Normal synchronous timeout is 30 seconds and is capped at 120 seconds. Results contain `id`, `ok`, `output` or `error`, `started_at`, and `ended_at`.

## Core

| type | args | output | authorization / limits |
|---|---|---|---|
| `ping` | none | `pong` | authenticated device channel |
| `system_info` | none | JSON OS/CPU/RAM/GPU/disks/boot/agent version | read-only |
| `process_list` | none | tasklist CSV | read-only |

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

`process_start`: args `path`, optional `args`. The executable path must exactly match one entry in `ANTHARES_ALLOWED_EXECUTABLES` (semicolon-separated absolute paths).

`process_kill`: arg `pid`. The agent resolves the executable path of the PID and permits termination only when it exactly matches `ANTHARES_ALLOWED_EXECUTABLES`. System PIDs 0–4 are always rejected.

`process_list` remains read-only and does not require the process allowlist.

## Windows services

`service_status`: arg `name`, read-only.

`service_start` / `service_stop`: arg `name`. Mutating operations require an exact case-insensitive match in `ANTHARES_ALLOWED_SERVICES` (semicolon-separated service names).

## Persistent jobs

`job_start`: args `command`, optional `name`; requires `ANTHARES_ALLOW_SHELL=1`; returns a 16-hex-character `job_id`.

`job_list`: optional `limit` (max 100), `include_command`.

`job_status`: `job_id`, optional `include_command`.

`job_logs`: `job_id`, optional `offset_bytes`, `max_bytes` (max 256 KiB), `tail_lines`.

`job_cancel`: `job_id`; terminates the stored process tree.

Long jobs use a separate hidden PowerShell process and persisted metadata under `%PROGRAMDATA%\\AntharesRemoteAgent\\jobs`.

## Concurrency and delivery

The polling loop accepts multiple jobs concurrently. `ANTHARES_MAX_CONCURRENT` defaults to 4 and is clamped to 1–8. Result delivery is retried up to five times with exponential delays. The agent channel requires HTTPS and bearer/device authentication.

## MCP mapping guidance

The MCP integration should expose one typed tool per capability rather than a generic unrestricted dispatcher. Mutating tools should preserve the agent's allowlists and should not add bypass parameters. Sensitive outputs (clipboard, screenshots, command output) should only be returned to the requesting authorized conversation and should not be copied into public logs.
