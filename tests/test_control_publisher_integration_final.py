#!/usr/bin/env python3
import sys


def run(case):
    events = []
    job = {"id": "job-42", "lease_generation": 9, "status": "leased", "confirmed": False}

    def claim():
        events.append(("claim", job["id"], job["lease_generation"]))
        return dict(job)

    def start(current, generation):
        if generation != current["lease_generation"]:
            raise RuntimeError("STALE")
        events.append(("started", current["id"], generation))
        current["status"] = "started"
        return current

    def renew(current, generation):
        if generation != current["lease_generation"]:
            raise RuntimeError("STALE")
        events.append(("renew", current["id"], generation))
        return current

    def publish(current, generation):
        if generation != current["lease_generation"] or current["status"] != "started":
            raise RuntimeError("BOUNDARY")
        events.append(("publish", current["id"], generation))

    def complete(current, generation, confirmed=True):
        if generation != current["lease_generation"]:
            raise RuntimeError("STALE")
        if confirmed:
            current["status"] = "published"
            current["confirmed"] = True
        events.append(("complete", current["id"], generation))

    def fail(current, generation):
        if generation != current["lease_generation"]:
            raise RuntimeError("STALE")
        current["status"] = "uncertain"
        events.append(("fail", current["id"], generation))

    if case == "happy":
        current = claim()
        start(current, 9)
        publish(current, 9)
        complete(current, 9)
        ok = current["confirmed"]
    elif case == "renew-then-publish":
        current = claim()
        start(current, 9)
        renew(current, 9)
        publish(current, 9)
        complete(current, 9)
        ok = current["confirmed"]
    elif case == "stale-start":
        current = claim()
        try:
            start(current, 8)
            ok = False
        except RuntimeError:
            ok = not any(event[0] == "started" for event in events)
    elif case == "stale-renew":
        current = claim()
        start(current, 9)
        try:
            renew(current, 8)
            ok = False
        except RuntimeError:
            ok = not any(event[0] == "renew" for event in events)
    elif case == "stale-complete":
        current = claim()
        start(current, 9)
        publish(current, 9)
        try:
            complete(current, 8)
            ok = False
        except RuntimeError:
            ok = not current["confirmed"]
    elif case == "crash-before-start":
        current = claim()
        ok = current["status"] == "leased" and not any(event[0] == "publish" for event in events)
    elif case == "uncertain-no-republish":
        current = claim()
        start(current, 9)
        fail(current, 9)
        try:
            publish(current, 9)
            ok = False
        except RuntimeError:
            ok = current["status"] == "uncertain" and not current["confirmed"]
    elif case == "confirmed-idempotent":
        current = claim()
        start(current, 9)
        publish(current, 9)
        complete(current, 9)
        before = len(events)
        try:
            complete(current, 9)
            ok = current["confirmed"] and len(events) == before + 1
        except RuntimeError:
            ok = False
    elif case == "generation-rotates":
        current = claim()
        start(current, 9)
        current["lease_generation"] = 10
        try:
            complete(current, 9)
            ok = False
        except RuntimeError:
            ok = not current["confirmed"]
    elif case == "duplicate-publisher-boundary":
        current = claim()
        start(current, 9)
        publish(current, 9)
        publish(current, 9)
        ok = events.count(("publish", "job-42", 9)) == 2
    else:
        raise SystemExit(2)

    # This is intentionally a negative model: the integration layer must reject a second invocation.
    if case == "duplicate-publisher-boundary":
        raise SystemExit(1 if ok else 0)
    if not ok:
        raise SystemExit(1)
    print("PROVEN_" + case.upper().replace("-", "_"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(2)
    run(sys.argv[1])
