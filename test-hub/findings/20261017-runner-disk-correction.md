# Runner system disk exhaustion corrected
STATUS: PARTIAL
AREA: github, storage
DATE: 2026-10-17
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/39075764332
JOB:117522671812
COMMIT: dc9990e
SUPERSEDES: test-hub/findings/20261017-runner-disk-lease.md
LEASE: CLOSED

Decisive GitHub check annotation: System.IO.IOException insufficient disk space writing C:\actions-runner\_diag\Worker_20261017-223712-utc.log. Source and long jobs passed; short step failed before logs could flush. This is local C: capacity, not WordPress storage quota. No evidence of a new editorial exception in remotely persisted logs.
Live inspection: C: had644816896 bytes free; incomplete work/live_b6gL9plY_6w.f136.mp4.part569478325bytes. Preserved by moving this exact file (no deletion) to D:\AntharesWork\anthares-clipper\runner-media\preserved-from-run-39075764332, after checking no matching active downloader. C free1214173184; D free16118849536 afterward. No unrelated files removed, no queue reset or publication.
Both producer entrypoints now configure scratch on D by default on Windows, optionally CORTES_RUNNER_MEDIA_ROOT. Existing ledger unchanged. Check8GiB media headroom and1GiB Windows system headroom before work, plus8GiB before every short. Failure explicitly identifies runner disk and preserves files. Runtime configure tested actual D path successfully.36 focused pytest tests passed; syntax and diff checks passed. Remote main freshly checked4a994529 before FF publication dc9990e. GitLab same paths queried returned404; no mirror.
No full production retest dispatched. Remaining limitation: C is still low; guard detects recurrence rather than deleting arbitrary owner data.8GiB is operational minimum, not guarantee for arbitrarily long full-source fallback. Existing short render cleanup/recovery lifecycle not refactored by this patch.
