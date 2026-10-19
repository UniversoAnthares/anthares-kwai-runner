# Anthares Remote, Browser and automatic WordPress mirror acceptance

STATUS: PROVEN
AREA: remote-control, browser-session, wordpress-mirror
DATE: 2026-10-18
LEASE_OWNER: codex-01a14ef0
SUPERSEDES: 20261018-2212-lease-mirror-acceptance.md
LEASE: CLOSED; no outstanding mirror mutation work.

## Anthares Remote — resolved and proven

The installed SYSTEM supervisor inherited an obsolete device credential even though the protected on-disk credential matched the published device hash. Recovery queue issues [312](https://github.com/UniversoAnthares/anthares-ara-queue/issues/312) and [313](https://github.com/UniversoAnthares/anthares-ara-queue/issues/313) identified the mismatch and reloaded the existing supervisor without rebooting Windows. Source correction: `8a08de61`. The MCP capabilities adapter also called a nonexistent backend route; it now verifies signed backend status before exposing the known capabilities contract. OAuth operation scopes, Ed25519 signatures and separate device authority remain enforced.

Final harmless create-new marker job `5b5552b19c2db00dc60eb35eced3380d` completed with exit 0, SYSTEM identity, one marker line and exactly one SYSTEM agent. Connected status and empty queued/leased/uncertain counts were verified. Unauthorized MCP requests returned 401. Existing rotation was preserved; no token appears in this report.

## Anthares Browser — resolved and proven

The dedicated `D:\AntharsWork\browser-profiles\AntharesGitLab` profile retained authenticated GitHub, GitLab and Vercel access. GitLab remember-me login was completed legitimately, with the user's personal GitHub confirmation where required. A graceful close and task-driven reopen preserved authenticated GitLab project navigation. CDP remains loopback-only on port 9223; the dedicated browser is muted and isolated from personal profiles.

`anthares-brouser/windows/ensure-administrative-session.ps1` checks browser ownership and profile before recovery. The installed limited current-user task `Anthares Administrative Browser` runs at logon and every five minutes, with overlapping executions ignored. Recovery test LastTaskResult=0 at 22:14:14Z. This browser task is not a dependency of cloud mirroring.

## GitHub → GitLab — resolved and proven

Implementation is in [PR 163](https://github.com/UniversoAnthares/anthares-kwai-runner/pull/163), merged at `ed4afd76662d3b334928443c17ceaf0b767d969b`. The primary executor is Vercel project `anthares-wordpress-mirror`, invoked by Cloudflare native cron `0 * * * *` (hourly). The scheduler configuration was read back from Cloudflare after deployment version `7d9094e3-c491-420a-a065-238b24470ba1`. Final deployed source revision was verified by a successful authenticated invocation returning `ed4afd76`. There is also a Vercel daily cron at 08:17 UTC; its next daily occurrence has not yet been observed.

Actual native scheduler acceptance used a temporary minute cadence. At 22:14:31Z, run `38403546-f7d2-4bf3-a351-f97821552c35` automatically propagated the new main commit, changing only the two QA manifests. Durable [audit commit fdab4e21](https://gitlab.com/UniversoAnthares/anthares-wordpress/-/commit/fdab4e21cfeb0409498652b1c17aa92d410689c1). The previous destination was checkpointed at `backup/auto-mirror/main/b71d25ae75907713e0a6f1d4628097ea6f7d3041`. Validation scheduling was disabled after acceptance and the cadence reduced to hourly. Cloudflare schedule propagation can temporarily retain the previous minute cadence.

Final independently fetched refs:

| Ref | GitHub | GitLab |
| --- | --- | --- |
| main | bc0c3dd9b06b5bb3d68b761db95ca02f71cf37aa | 2ee282c467e54170ad33e42b8a548ab41d52aeac |
| validation/mirror-20261018-e2e | 3eeeb80c42722d43abeb762fbeac6b825a20d5b7 | 2382d4ec9c85db997eafad6d6a47519a42c3e621 |

Git ancestry checks succeeded for both source refs inside their destination refs and for the original GitLab `f95e566771690b940bd64fb18680d7321eb8a120` inside main. The only final main tree difference is the intentionally preserved GitLab `.gitlab-ci.yml`. Different HEADs are expected because the destination preserves both histories. The existing `backup/pre-sync-2026-10-17` was not rewritten.

Independent hosted fallback [GitHub run 39171607462](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39171607462) completed successfully. Its actual mirror result `3b7aab6e-a004-49f5-8cfa-7424d0350584` records executor `github-actions`, merged the third isolated validation marker into `2382d4ec`, changed only `.mirror-validation-20261018.txt`, checkpointed `ca49cbeb`, and persisted [audit 9094ff67](https://gitlab.com/UniversoAnthares/anthares-wordpress/-/commit/9094ff679c4519ec7c5a236a1af81aeda8939e11). This fallback is manually dispatched and may depend on future CI quota; the hourly primary consumes neither GitHub Actions nor GitLab CI minutes.

Final main no-change run `96de6713-a991-4d97-b60d-d51e5bfb880e` returned IN_SYNC_PRESERVING_DESTINATION, unchanged destination `2ee282c4`, empty changed_paths and [audit 936a6880](https://gitlab.com/UniversoAnthares/anthares-wordpress/-/commit/936a6880aa66665bd776ff2a5d5bfbfbabcb0343). Native subsequent no-change runs also preserved the destination.

Safety acceptance: four meaningful merge/auth/conflict/idempotence tests passed; live concurrent invocation was fenced; controlled invalid source authentication on the isolated validation branch produced CONTROLLED_AUTH_REJECTED ([audit 307f608a](https://gitlab.com/UniversoAnthares/anthares-wordpress/-/commit/307f608aad218514d4ca6aec49742907b1eb9873)), followed by successful scheduled recovery. Unauthorized mirror and scheduler-status requests returned 401. Source/destination rechecks, per-ref expiring locks, immutable backups and optimistic pushes prevent destructive races; conflicts abort without updating main. No force push was used.

Credentials: source fine-grained token is Contents/Metadata read-only on the single WordPress repo; destination project token has write_repository only, with the role required by protected main. They expire 2027-01-16. Production credentials are sensitive Vercel environment secrets; the scheduler holds only its invocation secret; fallback credentials use a GitHub environment restricted to main. Renew by creating equally scoped replacement credentials, replacing the corresponding managed secrets, validating authentication and a no-change run, then revoking the old credentials. Never paste values into chat or audit logs.

Three obsolete local AutoSync scripts were reversibly retired with hash-verified nonexecuting original backups: they previously ignored failed merges after shallow fetches. No matching scheduled task or live process remained. The cloud primary has no Windows dependency. Windows was not powered off for acceptance, in accordance with the user's restriction; actual execution occurred in Cloudflare/Vercel and the independent GitHub-hosted runner. No paid service, new subscription or credit-card step was introduced.

## Related WordPress QA correction — resolved and proven

[PR 21](https://github.com/UniversoAnthares/anthares-wordpress/pull/21) added the three missing smoke tests to each of the identical QA manifests; runtime files were unchanged. Main commit `bc0c3dd9` passed the production Vercel QA build: [deployment 3yt3stV2fi7ncbwmionG33WMLy1X](https://vercel.com/lucasyahn-6808/anthares-wordpress-qa-runner/3yt3stV2fi7ncbwmionG33WMLy1X), READY. This commit was the real native scheduled main transfer above.

No anthares-clipper, CORTES-specific code, Android queues, competing SYSTEM authority, reboot, shutdown or user logoff was introduced. Source commits and final evidence were checked against current peer HEADs before publication. This report closes the acceptance lease.
