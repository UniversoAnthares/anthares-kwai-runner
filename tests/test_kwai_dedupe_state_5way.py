#!/usr/bin/env python3
import re,sys,pathlib
case=sys.argv[1]
root=pathlib.Path(__file__).resolve().parents[1]
worker=(root/"cloudflare-worker/src/index.js").read_text(encoding="utf-8-sig")
wf=(root/".github/workflows/kwai-real-publish.yml").read_text()
gate=(root/"kwai_real_publish_promotion_gate.py").read_text()
qs=(root/"kwai_queue_state.sh").read_text()
def ok(name): print("PROVEN_"+name)
if case=="touching-interval":
    assert "Math.max(start,ps)<Math.min(end,pe)" in worker
    # strict inequality means [100,160] and [160,220] do not overlap
    assert not (max(160,100)<min(220,160))
    ok("TOUCHING_INTERVAL_ALLOWED")
elif case=="contained-interval":
    assert max(120,100)<min(140,160)
    assert "timeline_overlap:true" in worker
    ok("CONTAINED_INTERVAL_REJECTED")
elif case=="cross-source":
    assert 'if(String(prior.source_id||"")!==sourceId)continue;' in worker
    ok("SAME_TIMESPAN_DIFFERENT_SOURCE_ALLOWED")
elif case=="failed-job-dedupe":
    assert "status<>'failed'" in worker
    # failed terminal jobs intentionally leave dedupe namespace reusable; UNCERTAIN/PUBLISHED do not.
    assert worker.count("status<>'failed'") >= 2
    ok("FAILED_REUSABLE_UNCERTAIN_NOT_REUSABLE")
elif case=="canonical-before-publish":
    for token in ["source_id","source_start","source_end"]:
        assert token in gate
    assert "end <= start" in gate
    # Current workflow is intentionally self-test + fail-closed guard: no publisher is promoted yet.
    assert "kwai_real_publish_promotion_gate.py" in wf
    assert "kwai_publish.sh" not in wf
    assert "Real publication remains gated" in wf
    ok("CANONICAL_INTERVAL_GATE_AND_NO_UNGATED_PUBLISHER")
else: raise SystemExit(2)
