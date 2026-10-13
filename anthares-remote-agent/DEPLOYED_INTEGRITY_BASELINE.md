# Phase 4 — deployed Windows ARA V4 integrity baseline

Captured 2026-10-13, device `DESKTOP-FTDK0HP`, installation root `C:\ProgramData\AntharesRemoteAgent`. These hashes describe **deployed files**, not necessarily the repository copies. Do not overwrite a running executable merely because a repository file differs.

| File | Bytes | SHA-256 |
|---|---:|---|
| anthares-remote-agent-v4.exe | 7418368 | C8BA6137A464720A5A95A290F4001BCE98489B92C4D93894B2AC5E22CCC2499E |
| run-agent-system-supervisor.ps1 | 5887 | 0C3893C648D6B38184CC5F0888B4B61BB4ACD0788D514D78737F96ED0161D268 |
| recovery-watchdog-loop.ps1 | 361 | 9408BCC016CDBEC860B45FEF6B3CA5AD23BB8CEB9DA3EEFFC49087D9F9F57226 |
| recovery-watchdog.ps1 | 7368 | 532020E44427819A90674A08DD3A4637A36B3BC7DB2D68E1C6E65CE8C2CBCF6E |
| agent-env.ps1 | 3348 | 164A9A939093CFE7AF2128F8A1E0184BBC377844513C1AB992AB12B0E277F115 |
| load-issue-queue-auth.ps1 | 2378 | 80BBCC64448F5957296BFB328CEC41465E9C5A716653913A020ADFF0789149FE |

## Safe reconciliation procedure

1. Keep SYSTEM V4 running while comparing local files with reviewed repository sources; record source commit and hashes.
2. Keep DPAPI secrets, tokens and host-specific configuration **out of repositories**. Backup installed versions before each change.
3. Stage replacement files separately, verify SHA-256, and use an atomic replacement/restart during a controlled maintenance window; rollback automatically if queue ping and supervisor recovery fail.
4. Maintain a single SYSTEM writer. Do not launch a parallel V4 that consumes the same queue.
5. Preserve hidden/noninteractive operation; never open foreground windows or reboot without authorization.

## Redundancy target (not yet verified)

- Source replicas: GitHub, GitLab, and a third independent Git host (e.g. Codeberg/Forgejo), with periodic mirror consistency checks and divergence alerts. Never assume a mirror is current without checking refs.
- Independent recovery storage: an owner-controlled backup service on a free third-party platform may hold **encrypted** configuration snapshots and immutable checksums. It is not a fourth active queue writer.
- Transport redundancy: private GitHub/GitLab issue queues with a shared durable idempotency ledger; never run both transports against separate state directories.
- If a provider fails, fail over without replaying side-effecting jobs in uncertain state. Report any unverified replica as pending.

## Validation evidence

The production binary hash was confirmed both during installation and via a subsequent remote read. The GitHub issue-queue ping was confirmed in #50 and #51. A live failover, three-way mirror, automated rollback, and post-reboot watchdog recovery are **not** yet proven.
