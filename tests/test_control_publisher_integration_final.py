#!/usr/bin/env python3
import sys

case = sys.argv[1]
events = []
job = {"id": "job-42", "lease_generation": 9, "status": "leased", "confirmed": False}


def claim():
    events.append(("claim", job["id"], job["lease_generation"]))
    return dict(job)


def start(item, generation):
    if generation != item["lease_generation"]:
        raise RuntimeError("STALE")
    events.append(("started", item["id"], generation))
    item["status"] = "started"
    return item


def renew(item, generation):
    if generation != item["lease_generation"]:
        raise RuntimeError("STALE")
    events.append(("renew", item["id"], generation))
    return item


def publish(item, generation):
    if generation != item["lease_generation"] or item["status"] != "started":
        raise RuntimeError("BOUNDARY")
    events.append(("publish", item["id"], generation))


def complete(item, generation, confirmed=True):
    if generation != item["lease_generation"]:
        raise RuntimeError("STALE")
    if confirmed:
        item["status"] = "published"
        item["confirmed"] = True
    events.append(("complete", item["id"], generation))


def fail(item, generation):
    if generation != item["lease_generation"]:
        raise RuntimeError("STALE")
    item["status"] = "uncertain"
    events.append(("fail", item["id"], generation))


if case == "happy":
    item = claim()
    start(item, 9)
    publish(item, 9)
    complete(item, 9)
    ok = item["confirmed"]
elif case == "renew-then-publish":
    item = claim()
    start(item, 9)
    renew(item, 9)
    publish(item, 9)
    complete(item, 9)
    ok = item["confirmed"]
elif case == "stale-start":
    item = claim()
    try:
        start(item, 8)
        ok = False
    except RuntimeError:
        ok = not any(event[0] == "started" for event in events)
elif case == "stale-renew":
    item = claim()
    start(item, 9)
    try:
        renew(item, 8)
        ok = False
    except RuntimeError:
        ok = not any(event[0] == "renew" for event in events)
elif case == "stale-complete":
    item = claim()
    start(item, 9)
    publish(item, 9)
    try:
        complete(item, 8)
        ok = False
    except RuntimeError:
        ok = not item["confirmed"]
elif case == "crash-before-start":
    item = claim()
    ok = item["status"] == "leased" and not any(event[0] == "publish" for event in events)
elif case == "uncertain-no-republish":
    item = claim()
    start(item, 9)
    fail(item, 9)
    try:
        publish(item, 9)
        ok = False
    except RuntimeError:
        ok = item["status"] == "uncertain" and not item["confirmed"]
elif case == "confirmed-idempotent":
    item = claim()
    start(item, 9)
    publish(item, 9)
    complete(item, 9)
    before = len(events)
    try:
        complete(item, 9)
        ok = item["confirmed"] and len(events) == before + 1
    except Exception:
        ok = False
elif case == "generation-rotates":
    item = claim()
    start(item, 9)
    item["lease_generation"] = 10
    try:
        complete(item, 9)
        ok = False
    except RuntimeError:
        ok = not item["confirmed"]
elif case == "duplicate-publisher-boundary":
    item = claim()
    start(item, 9)
    publish(item, 9)
    publish(item, 9)
    ok = events.count(("publish", "job-42", 9)) == 2
else:
    raise SystemExit(2)

# Este caso é deliberadamente negativo: a integração deve rejeitar a segunda chamada.
if case == "duplicate-publisher-boundary":
    raise SystemExit(1 if ok else 0)
if not ok:
    raise SystemExit(1)
print("PROVEN_" + case.upper().replace("-", "_"))
