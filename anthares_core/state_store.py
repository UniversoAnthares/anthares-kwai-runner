#!/usr/bin/env python3
"""Deterministic text state export/import for Anthares Core.

The Git-backed state file is human-auditable and avoids committing SQLite binaries.
It is not a secret store: payloads placed in the queue must not contain credentials.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

# Allow direct execution as `python3 anthares_core/state_store.py ...` from repo root.
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

FIELDS=("id","kind","payload","status","attempts","lease_owner","lease_token","lease_until","result","created_at","updated_at")


def export_state(db_path,out_path):
    db=sqlite3.connect(db_path)
    rows=[]
    try:
        for row in db.execute("SELECT id,kind,payload,status,attempts,lease_owner,lease_token,lease_until,result,created_at,updated_at FROM tasks ORDER BY created_at,id"):
            item=dict(zip(FIELDS,row))
            item["payload"]=json.loads(item["payload"])
            item["result"]=json.loads(item["result"]) if item["result"] else None
            rows.append(item)
    finally:
        db.close()
    doc={"schema":"anthares.core.state.v1","tasks":rows}
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    Path(out_path).write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return len(rows)


def import_state(state_path,db_path):
    from anthares_core.queue import connect
    doc=json.loads(Path(state_path).read_text(encoding="utf-8"))
    if doc.get("schema")!="anthares.core.state.v1":
        raise ValueError("unsupported state schema")
    db=connect(db_path)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("DELETE FROM tasks")
        for item in doc.get("tasks",[]):
            missing=[k for k in FIELDS if k not in item]
            if missing:
                raise ValueError("missing fields: "+",".join(missing))
            db.execute("""INSERT INTO tasks(id,kind,payload,status,attempts,lease_owner,lease_token,lease_until,result,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(
                item["id"],item["kind"],json.dumps(item["payload"],sort_keys=True),item["status"],int(item["attempts"]),
                item["lease_owner"],item["lease_token"],item["lease_until"],
                json.dumps(item["result"],sort_keys=True) if item["result"] is not None else None,
                int(item["created_at"]),int(item["updated_at"])))
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    finally:
        db.close()
    return len(doc.get("tasks",[]))


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
    e=sub.add_parser("export");e.add_argument("--db",required=True);e.add_argument("--out",required=True)
    i=sub.add_parser("import");i.add_argument("--state",required=True);i.add_argument("--db",required=True)
    a=p.parse_args()
    n=export_state(a.db,a.out) if a.cmd=="export" else import_state(a.state,a.db)
    print(json.dumps({"ok":True,"count":n,"command":a.cmd},sort_keys=True))

if __name__=="__main__":main()
