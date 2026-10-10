#!/usr/bin/env python3
"""Deterministic JSON export/import for Anthares Publisher ledger."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

FIELDS=("id","source_id","start_ms","end_ms","platform","account","content_sha256","status","external_id","public_url","attempts","created_at","updated_at")

def export_state(db_path,out_path):
    db=sqlite3.connect(db_path)
    try:
        rows=[dict(zip(FIELDS,row)) for row in db.execute("SELECT id,source_id,start_ms,end_ms,platform,account,content_sha256,status,external_id,public_url,attempts,created_at,updated_at FROM publications ORDER BY created_at,id")]
    finally: db.close()
    doc={"schema":"anthares.publisher.state.v1","publications":rows}
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    Path(out_path).write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return len(rows)

def import_state(state_path,db_path):
    from anthares_publisher.ledger import connect
    doc=json.loads(Path(state_path).read_text(encoding="utf-8"))
    if doc.get("schema")!="anthares.publisher.state.v1": raise ValueError("unsupported state schema")
    db=connect(db_path)
    try:
        db.execute("BEGIN IMMEDIATE");db.execute("DELETE FROM publications")
        for item in doc.get("publications",[]):
            if any(k not in item for k in FIELDS): raise ValueError("publication record missing required field")
            db.execute("""INSERT INTO publications(id,source_id,start_ms,end_ms,platform,account,content_sha256,status,external_id,public_url,attempts,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",tuple(item[k] for k in FIELDS))
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK");raise
    finally: db.close()
    return len(doc.get("publications",[]))

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    e=sub.add_parser('export');e.add_argument('--db',required=True);e.add_argument('--out',required=True)
    i=sub.add_parser('import');i.add_argument('--state',required=True);i.add_argument('--db',required=True)
    a=p.parse_args();n=export_state(a.db,a.out) if a.cmd=='export' else import_state(a.state,a.db)
    print(json.dumps({"ok":True,"command":a.cmd,"count":n},sort_keys=True))
if __name__=='__main__':main()
