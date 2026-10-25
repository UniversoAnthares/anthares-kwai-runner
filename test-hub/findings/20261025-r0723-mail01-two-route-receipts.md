# R07.23 — MAIL-01 real E2E and independent checks (25/10/2026)

**Owner:** ChatGPT; **job:** R07-23-ALL-20261025; **governance receipt:** f6fc9ca59a96e451, policy audit 218 repositories, 0 failures. **Scope:** read-only inspections plus controlled internal QA mail. **No publication, no pipeline trigger, no media upload, no password disclosure, no rollout.**

## Item 26 — MAIL-01 (acceptance within R07.6)

One controlled event marker: `ANTHARES-MAIL01-R0723-20261025-0825`; two independent delivery routes, one unique message to each independent destination:

| Route | Provider SEND | Provider READBACK | Result |
| --- | --- | --- | --- |
| A, Hostinger → Gmail | Hostinger 204 | Gmail message `1a17306e861d9ce8`, received `2026-10-25T12:26:31Z` | PASS: exactly 1 |
| B, Gmail → Hostinger | Gmail message `1a17306e50877ac4` | Hostinger INBOX UID `18`, received `2026-10-25T12:26:34Z`, search pagination `total=1` | PASS: exactly 1 |

Both messages were internal, benign, contained only the event marker, and had no secrets or attachments. READBACK at each destination was performed after sending. **Scoped R07.6 criterion met:** two alert delivery mechanisms, actual receipt and no duplicate per destination for this event. Not a claim of universal failover/DR policy or delivery guarantees under arbitrary failures.

## Item 09 — CORTES-ISO-04 limited QA roles, NOT completed

Project Neon `purple-flower-35918989`, branch QA `br-quiet-unit-b8w1tqmf`. Two QA role names created by SQL: `cortes_instagram_limited_r0723` and `cortes_threads_limited_r0723`, each LOGIN=true, BYPASSRLS=false, CREATEROLE=false, SUPERUSER=false, INHERIT=true. SQL-grant attempt for Instagram was refused by tool security; it **was not repeated through another channel**. Threads membership grant accepted. Direct `run_sql(role_name=...)` access as Threads role returned `missing authentication credentials: required password`. No usable credentials provisioned, no runtime owner linked, no publish rights, no production schema change. SQL owner on production still has BYPASSRLS; login proof and real cross-network DML DENIED remain outstanding. Do **not** count QA metadata as complete account isolation.

## Item 22 — MEDIA-01 status remains PARTIAL

Windows task `Anthares CORTES F1 Google Drive Replica 30min` last ran 25/10/2026 07:59:59 America/Campo_Grande, result 0, next run 08:29:29. Inspected `runner-media/output` and `runner-media/shorts`: no MP4 in those paths, so the acceptance of a **new** master with two SHA restores was **not** met.

## Risks / blockers

- Windows disk free storage still low, fluctuating. Do not start large restore/installer on the host or delete other agents' files without ownership evidence.
- Attempted directory inventory and an unrelated workflow source write were blocked by safety controls; no alternate mechanism used to circumvent them.
- Items 26 only is promoted to COMPLETE based on above receipt and the narrow official R07.6 acceptance. All other IDs retain prior evidence/status.

**Rollback:** No production change to roll back; the two controlled QA messages are retained as delivery receipts. This is an evidence-only draft; human review before merge. **Canonical checklist:** https://docs.google.com/document/d/1SkjpRPJYLe9n_9SDOA4s-RibN8Pb_hm6-ukS6pbV7aQ/edit.
