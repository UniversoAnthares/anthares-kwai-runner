#!/usr/bin/env python3
"""Allowlisted Anthares Core worker.

Only explicit task kinds are executable. Queue payloads are data, never shell commands.
"""
import argparse
import json
import os
import platform
from datetime import datetime, timezone

from anthares_core.queue import connect, claim, finish


def execute(task):
    kind=task["kind"]
    payload=task["payload"]
    if kind=="probe":
        return {"ok":True,"kind":"probe","target":payload.get("target"),
                "worker_os":platform.system(),"github_actions":bool(os.getenv("GITHUB_ACTIONS")),
                "completed_at":datetime.now(timezone.utc).isoformat()}
    raise ValueError(f"unsupported task kind: {kind}")


def run(db_path,worker,max_tasks=10):
    db=connect(db_path);done=[]
    try:
        for _ in range(max_tasks):
            task=claim(db,worker,120)
            if not task: break
            try:
                result=execute(task)
                accepted=finish(db,task["id"],task["token"],result,True)
            except Exception as exc:
                result={"ok":False,"error":type(exc).__name__,"message":str(exc)[:300]}
                accepted=finish(db,task["id"],task["token"],result,False)
            if not accepted:
                raise RuntimeError("lease lost before task completion")
            done.append({"id":task["id"],"result":result})
    finally:
        db.close()
    return done


def main():
    p=argparse.ArgumentParser();p.add_argument("--db",required=True);p.add_argument("--worker",required=True);p.add_argument("--max-tasks",type=int,default=10)
    a=p.parse_args();print(json.dumps({"processed":run(a.db,a.worker,a.max_tasks)},sort_keys=True))

if __name__=="__main__":main()
