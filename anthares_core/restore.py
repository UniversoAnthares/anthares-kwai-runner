#!/usr/bin/env python3
"""Restore latest safe Anthares Core snapshot from an artifact directory."""
import argparse
import json
import sqlite3
from pathlib import Path

def verify(path):
    db=sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro",uri=True)
    try:
        assert db.execute("PRAGMA quick_check").fetchone()[0]=="ok"
        tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "tasks" in tables
        count=db.execute("SELECT count(*) FROM tasks").fetchone()[0]
        return count
    finally:
        db.close()

def restore(source,target):
    source,target=Path(source),Path(target)
    count=verify(source)
    target.parent.mkdir(parents=True,exist_ok=True)
    # SQLite backup API yields consistent destination even if source uses WAL.
    src=sqlite3.connect(f"file:{source.resolve()}?mode=ro",uri=True)
    tmp=target.with_name(target.name+".incoming")
    try:
        dst=sqlite3.connect(tmp)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    verify(tmp)
    tmp.replace(target)
    return {"restored":True,"task_count":count,"target":str(target)}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--target",required=True)
    a=p.parse_args()
    print(json.dumps(restore(a.source,a.target),sort_keys=True))
