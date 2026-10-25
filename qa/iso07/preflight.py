"""Diagnóstico R07.6 CORTES-ISO-07, estritamente leitura; nunca autoriza publicação.

O relatório exige validação externa independente para os gates de IAM, banco,
conta, mídia, exclusividade e rollback. Campos locais podem ser forjados:
nenhum resultado deste utilitário concede permissão para executar o publicador.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NETWORK = "tiktok"
ACCOUNT = "lucasrosalem4"
ENVIRONMENT = "cortes-tiktok-lucas4"
REQUIRED_TABLES = (
    "cortes_publications",
    "cortes_tiktok_lucasrosalem4_publications",
)
OWNERSHIP_GATES = (
    "platform_owner_verified",
    "secret_scope_verified",
    "independent_deploy_identity_verified",
    "external_release_approved",
    "deploy_authorized",
)
ATTESTATION_GATES = (
    "two_independent_non_admin_principals_verified",
    "cross_network_denied_both_directions",
    "production_single_writer_fencing_verified",
    "uncertain_ledger_reconciled",
    "media_editorial_identity_verified",
    "quota_and_cost_approved",
    "rollback_isolated_verified",
    "external_receipt_validation_ready",
)
ENV_REGEX = re.compile(r"(?m)^[ ]{4}environment:\s*['\"]?" + re.escape(ENVIRONMENT) + r"['\"]?\s*(?:#.*)?$")
FOREIGN_SECRETS = ("KWAI_PASSWORD", "INSTAGRAM_STORAGE_STATE", "THREADS_STORAGE_STATE")


def inspect(cloud: str, fallback: str, ownership: dict | None,
            database: dict | None, attestation: dict | None) -> dict:
    blocked: list[str] = []
    ownership = ownership if isinstance(ownership, dict) else {}
    database = database if isinstance(database, dict) else {}
    attestation = attestation if isinstance(attestation, dict) else {}

    if ownership.get("network") != NETWORK or ownership.get("account") != ACCOUNT:
        blocked.append("owner_network_account_mismatch")

    for label, source in (("cloud", cloud), ("windows_fallback", fallback)):
        if not ENV_REGEX.search(source or ""):
            blocked.append(f"{label}_environment_unbound")
        if "secrets.TIKTOK_LUCASROSALEM4_STORAGE_STATE" not in (source or ""):
            blocked.append(f"{label}_account_secret_reference_missing")
        for foreign in FOREIGN_SECRETS:
            if re.search(r"\b" + re.escape(foreign) + r"\b", source or ""):
                blocked.append(f"{label}_foreign_secret_reference_{foreign.lower()}")

    for key in OWNERSHIP_GATES:
        if ownership.get(key) is not True:
            blocked.append(f"ownership_{key}_unverified")

    tables = database.get("tables", {})
    if not isinstance(tables, dict):
        tables = {}
    for table in REQUIRED_TABLES:
        detail = tables.get(table)
        if not isinstance(detail, dict):
            detail = {}
        for field in ("rls_enabled", "force_rls"):
            if detail.get(field) is not True:
                blocked.append(f"database_{table}_{field}_unverified")
        policies = detail.get("policies")
        if type(policies) is not int or policies < 1:
            blocked.append(f"database_{table}_policy_missing")

    if database.get("production_principal_bypassrls") is not False:
        blocked.append("database_production_principal_nobypassrls_unverified")
    for key in ATTESTATION_GATES:
        if attestation.get(key) is not True:
            blocked.append(f"external_{key}_unverified")

    # As declarações recebidas são material de auditoria e não evidência autenticada.
    # Mesmo sem lacunas declaradas, uma autoridade independente deve obter provas
    # diretamente dos provedores; nenhuma chamada a publicador está implementada.
    return {
        "schema": 1,
        "control": "R07.6-13/CORTES-ISO-07",
        "network": NETWORK,
        "account": ACCOUNT,
        "status": "BLOCKED" if blocked else "REVIEW_REQUIRED",
        "blocked_gates": sorted(set(blocked)),
        "claims_are_untrusted": True,
        "authorized_to_publish": False,
        "live_publication_invoked": False,
    }


def _json(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as reader:
        data = json.load(reader)
    if not isinstance(data, dict):
        raise ValueError("Evidence root must be a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="ISO-07 read-only admission diagnostics")
    parser.add_argument("--cloud", required=True, type=Path)
    parser.add_argument("--fallback", required=True, type=Path)
    parser.add_argument("--ownership", type=str)
    parser.add_argument("--database", type=str)
    parser.add_argument("--attestation", type=str)
    args = parser.parse_args()
    report = inspect(
        args.cloud.read_text(encoding="utf-8"),
        args.fallback.read_text(encoding="utf-8"),
        _json(args.ownership),
        _json(args.database),
        _json(args.attestation),
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
