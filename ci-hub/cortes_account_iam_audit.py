#!/usr/bin/env python3
"""Fail-closed, read-only TikTok account IAM/CI audit. No provider secrets accessed."""
import argparse
import json
import re
from pathlib import Path

class BoundaryDenied(ValueError):
    pass

EXPECTED = {
    "network": "tiktok",
    "account": "lucasrosalem4",
    "repository": "UniversoAnthares/anthares-kwai-runner",
    "environment": "cortes-tiktok-lucas4",
    "credential_name": "CORTES_TIKTOK_LUCAS4_STORAGE_STATE",
    "runtime_variable": "TIKTOK_LUCASROSALEM4_STORAGE_STATE",
    "publisher_code": "tools/cortes_tiktok_lucasrosalem4_cloud_publish.py",
    "queue_code": "infra/neon-cortes-lucasrosalem4/index.mjs",
    "queue_table": "cortes_tiktok_lucasrosalem4_publications",
}
WORKFLOWS = (
    ".github/workflows/cortes-tiktok-lucasrosalem4-cloud-publisher.yml",
    ".github/workflows/cortes-tiktok-lucasrosalem4-windows-fallback.yml",
)
REF = re.compile(r"secrets\.([A-Za-z_][A-Za-z0-9_]*)")

def validate_manifest(m):
    for key, value in EXPECTED.items():
        if m.get(key) != value:
            raise BoundaryDenied("account_binding_invalid_" + key)
    if m.get("schema") != 1 or m.get("consumer_workflows") != list(WORKFLOWS):
        raise BoundaryDenied("workflow_manifest_invalid")
    # Never permit the manifest itself to attest external IAM or a deploy.
    for name in ("platform_owner_verified", "secret_scope_verified",
                 "independent_deploy_identity_verified", "external_release_approved",
                 "deploy_authorized"):
        if m.get(name) is not False:
            raise BoundaryDenied("self_attested_authority_denied_" + name)
    return m

def assert_actor(m, network, account, workflow):
    if network != m["network"] or account != m["account"]:
        raise BoundaryDenied("cross_network_identity_denied")
    if workflow not in m["consumer_workflows"]:
        raise BoundaryDenied("foreign_workflow_denied")

def inspect_workflow(m, text, workflow):
    if not isinstance(text, str) or len(text) > 160_000:
        raise BoundaryDenied("workflow_invalid")
    refs = set(REF.findall(text))
    if refs != {m["credential_name"]}:
        raise BoundaryDenied("foreign_or_missing_secret_denied")
    if not re.search(r"(?m)^\s*contents:\s*read\s*$", text):
        raise BoundaryDenied("contents_permission_denied")
    if not re.search(r"(?m)^\s*id-token:\s*write\s*$", text):
        raise BoundaryDenied("signed_oidc_capability_required")
    if re.search(r"(?m)^\s*(?:actions|deployments|issues|packages|pull-requests):\s*write\s*$", text):
        raise BoundaryDenied("excessive_workflow_permission_denied")
    if not re.search(r"(?m)^\s*group:\s*cortes-tiktok-lucas(?:rosalem4|4)-", text):
        raise BoundaryDenied("unowned_concurrency_group_denied")
    env = re.search(r"(?m)^\s*environment:\s*(?:name:\s*)?([A-Za-z0-9_-]+)\s*$", text)
    status = "SHADOW_CONTRACT_VALID" if env and env.group(1) == m["environment"] else "BLOCKED_ACCOUNT_ENVIRONMENT_NOT_BOUND"
    return {"workflow": workflow, "status": status, "secret_refs": sorted(refs),
            "secrets_values_read": False, "deploy_authorized": False}

def audit(root, m, *, actor_network="tiktok", actor_account="lucasrosalem4"):
    validate_manifest(m)
    root = Path(root).resolve(strict=True)
    checks = []
    for workflow in WORKFLOWS:
        assert_actor(m, actor_network, actor_account, workflow)
        path = root / workflow
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
            raise BoundaryDenied("workflow_path_escape_denied")
        checks.append(inspect_workflow(m, path.read_text(encoding="utf-8"), workflow))
    pub = (root / m["publisher_code"]).read_text(encoding="utf-8")
    neon = (root / m["queue_code"]).read_text(encoding="utf-8")
    if 'ACCOUNT="lucasrosalem4"' not in pub or "cortestiktok4.compute" not in pub:
        raise BoundaryDenied("publisher_identity_or_queue_mismatch")
    for fragment in (m["queue_table"], "job_workflow_ref", "RS256",
                     "token.actions.githubusercontent.com"):
        if fragment not in neon:
            raise BoundaryDenied("signed_oidc_queue_binding_missing")
    status = "BLOCKED_PROVISIONING" if any(c["status"].startswith("BLOCKED") for c in checks) else "SHADOW_CONTRACT_VALID"
    return {"status": status, "network": m["network"], "account": m["account"],
            "checks": checks, "deploy_authorized": False, "provider_iam_verified": False,
            "pending": ["prove native secret has no repository or organization alias", "revoke old repo secret after canary",
                        "distinct real OIDC identity and deploy principal", "deny/allow with real principals",
                        "account-specific recovery and rollback"]}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--expect-blocked", action="store_true")
    a = p.parse_args()
    try:
        result = audit(a.root, json.loads(Path(a.manifest).read_text(encoding="utf-8")))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if a.expect_blocked and result["status"] == "BLOCKED_PROVISIONING" else 3
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "DENIED", "reason": str(exc)[:160],
                          "deploy_authorized": False}))
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
