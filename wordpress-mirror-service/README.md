# Anthares WordPress safe mirror

Source: `UniversoAnthares/anthares-wordpress` on GitHub, branch `main`.
Destination: the same project on GitLab. GitLab-only CI configuration is retained.

## Execution

The primary executor is the Vercel project `anthares-wordpress-mirror`. A small native
Cloudflare Cron Trigger calls its authenticated `/api/sync` route hourly. Vercel also
registers a daily native cron (`08:17 UTC`) as an independent scheduler. Neither path
uses GitHub/GitLab CI minutes or the personal computer.

`.github/workflows/wordpress-safe-mirror-fallback.yml` in the runner repository is a
manual independent GitHub-hosted executor. It runs this same implementation and shares
the same GitLab lock/audit refs. Its credentials are environment Secrets restricted to
the runner repository's `main` branch. Existing WordPress CI remains optional.

Native scheduler acceptance on 2026-10-18 transferred the isolated marker in run
`e25e34dc-d0e5-49aa-9aaa-1e3642d9d24e`. The subsequent native main run
`38403546-f7d2-4bf3-a351-f97821552c35` transferred actual QA fix `bc0c3dd9`
to destination `2ee282c4`, preserving GitLab-only CI. Permanent audit commit:
[`fdab4e21`](https://gitlab.com/UniversoAnthares/anthares-wordpress/-/commit/fdab4e21cfeb0409498652b1c17aa92d410689c1).
Production scheduling was then reduced from the temporary minute acceptance cadence
to `0 * * * *`; the scheduled validation branch was disabled.

## Preservation and concurrency

The existing WordPress `qa/anthares-safe-mirror.sh` was inspected first. Its ancestry,
tree comparison and no-force-push principles are retained here. The Node implementation
adds a clean three-way merge, per-ref serialization, compare-and-swap fencing, immutable
backup refs and durable results without requiring a native Git binary in a function.

Each run acquires `mirror-state/wordpress/main` with a normal fast-forward push of a
unique lease commit. Competing commits cannot both advance that ref. The lease expires
after ten minutes, longer than the maximum five-minute Vercel execution or eight-minute
fallback job. Ownership and both provider HEADs are checked again before writing.

When GitLab already contains the source, the run leaves `main` unchanged. Identical HEADs
are not required: GitLab may legitimately contain its own CI settings and merge history.
Clean merges preserve both parents; content conflicts stop the run. Before a destination
change, `backup/auto-mirror/<ref>/<old-head>` preserves the previous destination. Pushes
must match the exact expected old ref, never use force, and are verified afterward.

`mirror-state/wordpress/main` stores bounded JSON in commit messages: run ID, trigger,
source/destination HEADs, outcome, changed paths, checkpoint, time and executor revision.
The Cloudflare scheduler also retains seven days of run records in its dedicated KV
namespace. `/status` and `/api/sync?status=1` require the service credential.

## Secrets and renewal

- `GITHUB_READ_TOKEN`: fine-grained token scoped only to the WordPress repository;
  Contents and Metadata read-only.
- `GITLAB_WRITE_TOKEN`: project token scoped only to WordPress, `write_repository`;
  Maintainer is required by protected `main`.
- `CRON_SECRET`: random invocation credential shared only by Vercel and the scheduler.

Repository tokens expire **2027-01-16**. Renew with the same scopes before that date;
replace production Vercel Secrets and the two GitHub environment Secrets, redeploy the
executor, then test the isolated validation ref before revoking the previous tokens.
The scheduler needs no repository token. Never put secret values in a command argument,
Git URL, issue, log, README or commit. Windows staging copies are DPAPI protected.

## Validation

`npm ci --ignore-scripts && npm test` covers preservation, history, conflict refusal,
idempotence, authorization and the ref allowlist. The isolated
`validation/mirror-20261018-e2e` branch supports real acceptance tests; it is not a
publication route. An explicit authentication fault on that ref sends an invalid token
to the private source, expects HTTP rejection, records the diagnostic and releases the
lease. Fault probes on `main` are rejected.

The personal PC is only an administrative console. The dedicated administrative browser
uses `D:\AntharsWork\browser-profiles\AntharesGitLab`, loopback CDP `9223`, muted audio
and hidden Chromium. `anthares-brouser/windows/ensure-administrative-session.ps1` recovers
that profile without reusing personal profiles or changing publishing executors.
