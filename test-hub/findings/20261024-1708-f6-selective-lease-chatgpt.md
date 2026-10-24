# Lease F6 — seleção real Forgejo por falha simulada dos provedores anteriores
owner: chatgpt
job: forgejo-f6-selective-proof-20261024
started_utc: 2026-10-24T17:08:00Z
expires_utc: 2026-10-24T18:08:00Z
scope: UniversoAnthares/anthares-wordpress/qa/ara-failover-chain.py, qa/ARA-FAILOVER-CHAIN.md and QA manifest references if adding files.
baseline: ae88e2e766ad4e489dd7e2eb05fc39096f249ed6
independent_external_qa_evidence: Hostinger Forgejo authenticated API run #181 success, same baseline SHA.
purpose: add safe --test-forgejo-selection (inject only the four preceding stages, preserve authentic Forgejo API proof, isolated trace, no Windows QA execution, no synthetic PASS), test real evidence, sync code, and repeat QA at changed SHA if necessary.
separation: no CORTES code, queues, secrets or services; no security-guard bypass. No uninstall/reboot or production provider disruption. Read before write; recheck HEAD and reconcile concurrency.
