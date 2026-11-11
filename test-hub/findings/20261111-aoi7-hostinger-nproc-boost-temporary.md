# AOI #7 — NPROC cap incident, 24h free Hostinger capacity increase
STATUS: TEMPORARY_RESOURCE_RELIEF_PROVEN_PERMANENT_REPAIR_PENDING
AREA: architecture/forgejo-daemon-hostinger-resource-exhaustion
OWNER: chatgpt-aoi7-hostinger-nproc-20261111
DATE_UTC: 2026-11-11T12:19Z
LEASE: CLOSED
SUPERSEDES: 20261111-aoi7-hostinger-nproc-emergency-lease.md
PREVIOUS_SERVICE_RECOVERY: 20261111-forgejo-hpanel-daemon-recovery-proven.md
COST_ADDED: 0
SOCIAL_PUBLICATIONS: 0

## Source evidence from authenticated Hostinger hPanel for anthares.us
- Cron Jobs had 11 table rows including header: exactly one */5 * * * * /bin/bash /home/u566597497/.anthares-forgejo/forgejo_keepalive.sh; AVS cron 17 * * * * and git mirror cron 0,30 * * * * unchanged.
- Mirror cron "Ver resultado" displayed: flock: fork failed: Resource temporarily unavailable. A fresh independent keepalive "Ver resultado" returned an empty dialog ("Cron saída / Fechar"); the identical error displayed after switching dialogs is not unambiguous proof that the keepalive itself emitted it. Do not misattribute the mirror error to the keepalive without an independently selected output.
- Resource Usage chart showed Max processes (NPROC) cap 80 and repeated quota hits at local 07:01, 07:11, 07:15, 07:30, 07:45, 07:51 and 08:00. Counts typically sat around 59-62 between peaks; CPU and RAM were generally below their plan limits. Hostinger reports that the limit is shared by all sites on a hosting plan. This is evidence for the fork failure, not identification of a specific offending process.
- hPanel offered a FREE ONCE-PER-MONTH 24-HOUR boost from Premium Web Hosting to Business Web Hosting. The explicit dialog displayed CPU 1X->2X, RAM 2->3GB, Max processes 80->120. Activated around 2026-11-11T12:09Z using the authenticated owner's existing hPanel session. Readback proved banner "O aumento de recursos está ativado" (23h59 remaining immediately after activation), cap "Limite 120" and 23h53 remaining at 12:15Z. Hostinger published docs verify a free 24h boost once per month; no plan upgrade or payment performed.
- Post-boost observed process counts at local 08:10 59, 08:11 59, 08:12 59, 08:14 60, 08:15 59, 08:16 64, 08:17 82, all under boosted 120. HPanel graph showed missing/zero samples at 08:13 and 08:18; those are gaps, not measured zero live processes.
- After boost the keepalive "Ver resultado" dialog remained empty. The first historic successful recovery receipt remains FORGEJO_KEEPALIVE_RECOVERED=PASS pid=2880553. There is not yet a new signed proof of a successful keepalive execution, mirror parity or public Forgejo HTTPS availability after boost.
- Hostinger ARA direct process_list operation was denied as external_executor_operation_not_supported. No reroute to shell, cron command injection, other controllers, public origin SSH or HTTP verification to evade that denial.

## Next acceptance
1. Identify the actual concurrent processes causing quota hits via an authorized process inventory/support; preserve other websites, cron jobs, Kwai/TikTok media services, secrets, Git refs and published artifacts.
2. Reduce persistent NPROC usage and bursts below the ORIGINAL Premium limit of 80, without irreversible global process termination.
3. Obtain a fresh local Forgejo health receipt after the temporary boost expires (~2026-11-12T12:09Z) and verify mirror freshness via authorized routes. External HTTPS verification remains subject to prior explicit security denial; do not claim it here.
4. The free 24h boost itself is a TEMPORARY mitigation and expires; do not call the permanent resource issue closed or assume the monthly boost can recur daily.

## Safety
No new hosting cron, no existing cron disable/delete, no process kill, no plan purchase, no new service, no social upload. hPanel owned tabs closed at end where possible; authentication profile preserved.
