import importlib.util
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("anthares_control_plane_app", APP_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

TOKEN = "test-secret"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def make_client(tmp_path):
    app = mod.create_app(str(tmp_path / "cp.db"), TOKEN)
    app.config.update(TESTING=True)
    return app.test_client()


def create_job(c, idem="job-1", payload=None, dedupe="video:abc"):
    return c.post(
        "/v1/jobs",
        json={
            "idempotency_key": idem,
            "dedupe_key": dedupe,
            "kind": "publish",
            "payload": payload or {"video": "a.mp4"},
            "max_attempts": 3,
        },
        headers=HEADERS,
    )


def test_health_and_auth(tmp_path):
    c = make_client(tmp_path)
    assert c.get("/health").status_code == 200
    assert c.get("/v1/stats").status_code == 401
    assert c.get("/v1/stats", headers=HEADERS).status_code == 200


def test_idempotency_same_request_returns_same_job(tmp_path):
    c = make_client(tmp_path)
    a = create_job(c)
    b = create_job(c)
    assert a.status_code == 201
    assert b.status_code == 200
    assert a.get_json()["job"]["id"] == b.get_json()["job"]["id"]


def test_idempotency_conflict_is_rejected(tmp_path):
    c = make_client(tmp_path)
    assert create_job(c).status_code == 201
    r = create_job(c, payload={"video": "different.mp4"})
    assert r.status_code == 409
    assert r.get_json()["error"] == "idempotency_conflict"


def test_dedupe_key_collapses_different_idempotency_keys(tmp_path):
    c = make_client(tmp_path)
    a = create_job(c, idem="a", dedupe="sha256:one")
    b = create_job(c, idem="b", dedupe="sha256:one")
    assert a.status_code == 201
    assert b.status_code == 200
    assert a.get_json()["job"]["id"] == b.get_json()["job"]["id"]


def test_lease_heartbeat_complete_and_stale_fencing(tmp_path):
    c = make_client(tmp_path)
    created = create_job(c).get_json()["job"]
    claim = c.post("/v1/jobs/next", json={"executor_id": "exec-1", "ttl_seconds": 60}, headers=HEADERS)
    assert claim.status_code == 200
    job = claim.get_json()
    assert job["id"] == created["id"]
    lease = {
        "executor_id": "exec-1",
        "lease_token": job["lease_token"],
        "lease_generation": job["lease_generation"],
    }
    assert c.post(f"/v1/jobs/{job['id']}/heartbeat", json=lease, headers=HEADERS).status_code == 200
    bad = dict(lease)
    bad["lease_generation"] += 1
    assert c.post(f"/v1/jobs/{job['id']}/complete", json={**bad, "result": {}}, headers=HEADERS).status_code == 409
    done = c.post(
        f"/v1/jobs/{job['id']}/complete",
        json={**lease, "result": {"publication_id": "p1"}},
        headers=HEADERS,
    )
    assert done.status_code == 200
    state = c.get(f"/v1/jobs/{job['id']}", headers=HEADERS).get_json()
    assert state["status"] == "completed"
    assert state["result"]["publication_id"] == "p1"


def test_standby_refuses_claims_and_promotion_changes_epoch(tmp_path):
    c = make_client(tmp_path)
    create_job(c)
    before = c.get("/health").get_json()["epoch"]
    r = c.post("/v1/admin/role", json={"role": "standby"}, headers=HEADERS)
    assert r.status_code == 200
    assert r.get_json()["epoch"] == before + 1
    claim = c.post("/v1/jobs/next", json={"executor_id": "exec-1"}, headers=HEADERS)
    assert claim.status_code == 503
    promote = c.post("/v1/admin/role", json={"role": "active"}, headers=HEADERS)
    assert promote.status_code == 200
    claim2 = c.post("/v1/jobs/next", json={"executor_id": "exec-1"}, headers=HEADERS)
    assert claim2.status_code == 200


def test_failure_requeues_until_max_attempts_then_dead(tmp_path):
    c = make_client(tmp_path)
    created = c.post(
        "/v1/jobs",
        json={
            "idempotency_key": "fail-job",
            "kind": "publish",
            "payload": {},
            "max_attempts": 1,
        },
        headers=HEADERS,
    ).get_json()["job"]
    job = c.post("/v1/jobs/next", json={"executor_id": "exec-1"}, headers=HEADERS).get_json()
    r = c.post(
        f"/v1/jobs/{created['id']}/fail",
        json={
            "executor_id": "exec-1",
            "lease_token": job["lease_token"],
            "lease_generation": job["lease_generation"],
            "error": {"code": "test"},
        },
        headers=HEADERS,
    )
    assert r.status_code == 200
    assert r.get_json()["status"] == "dead"


def test_executor_registry(tmp_path):
    c = make_client(tmp_path)
    r = c.post(
        "/v1/executors/heartbeat",
        json={"executor_id": "browser-1", "capabilities": ["browser"], "metadata": {"host": "hidden"}},
        headers=HEADERS,
    )
    assert r.status_code == 200
    rows = c.get("/v1/executors", headers=HEADERS).get_json()["executors"]
    assert rows[0]["id"] == "browser-1"
    assert rows[0]["healthy"] is True
