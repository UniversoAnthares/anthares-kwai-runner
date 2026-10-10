"""Anthares autonomous control-plane: dependency gates and auditable state."""
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

TASKS = {
    "remote_identity": (),
    "persistent_session": ("remote_identity",),
    "publish_proof": ("persistent_session",),
    "unattended_runner": ("publish_proof",),
}
VALID = {"pending", "blocked", "verified"}

@dataclass
class Evidence:
    task: str
    status: str
    source: str
    detail: str
    observed_at: str

def evaluate(records):
    latest = {}
    for row in records:
        if row["task"] not in TASKS or row["status"] not in VALID:
            raise ValueError("invalid evidence")
        if not row.get("source") or not row.get("observed_at"):
            raise ValueError("missing provenance")
        latest[row["task"]] = row
    output = {}
    for task, deps in TASKS.items():
        row = latest.get(task)
        deps_ok = all(output[d]["status"] == "verified" for d in deps)
        if row and row["status"] == "verified" and deps_ok:
            status = "verified"
        elif not deps_ok:
            status = "blocked"
        else:
            status = row["status"] if row else "pending"
        output[task] = {"status": status, "depends_on": list(deps),
                        "evidence": row if status == "verified" else None}
    return output

def main():
    root = Path(__file__).resolve().parent
    records = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    state = evaluate(records)
    print(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                      "tasks": state}, ensure_ascii=False, indent=2))
    if any(x["status"] != "verified" for x in state.values()):
        raise SystemExit(2)

if __name__ == "__main__":
    main()
