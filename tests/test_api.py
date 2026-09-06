from fastapi.testclient import TestClient
from src.main import app


def _clean_db():
    from src.main import _connect

    with _connect() as conn:
        conn.execute("delete from records")


def test_health():
    with TestClient(app) as client:
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["ok"] is True


def test_workflow_create_and_run():
    _clean_db()
    wf = {
        "name": "Test Pipe",
        "steps": [
            {"name": "Search", "tool": "search", "params": {"query": "test"}},
            {"name": "Export", "tool": "export", "params": {"format": "csv"}},
        ],
    }
    with TestClient(app) as client:
        client.post("/api/workflows", json=wf)
        data = client.get("/api/workflows").json()
        assert len(data["workflows"]) >= 1
        run_res = client.post("/api/workflows/Test Pipe/run").json()
        assert run_res["total_steps"] == 2


def test_no_wildcard_cors():
    """No CORS middleware: responses must not carry permissive CORS headers."""
    with TestClient(app) as client:
        r = client.get("/api/health", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in r.headers


def test_workflow_collision_is_409_not_silent_overwrite():
    """'a_b' and 'a b' both sanitize to 'a_b' — the second must not silently
    overwrite the first's saved file (409 instead)."""
    _clean_db()
    from src.main import WORKFLOWS_DIR

    # Remove any saved workflow files so the test starts from a clean dir
    # (the earlier suite runs persisted a_b.json on disk).
    for f in WORKFLOWS_DIR.glob("*.json"):
        f.unlink()
    with TestClient(app) as client:
        r1 = client.post(
            "/api/workflows",
            json={
                "name": "a_b",
                "steps": [{"name": "s", "tool": "search", "params": {}}],
            },
        )
        assert r1.status_code == 200
        r2 = client.post(
            "/api/workflows",
            json={
                "name": "a b",
                "steps": [{"name": "s", "tool": "search", "params": {}}],
            },
        )
        assert r2.status_code == 409
        # The original is intact.
        assert client.post("/api/workflows/a_b/run").status_code == 200


def test_empty_steps_rejected():
    with TestClient(app) as client:
        r = client.post("/api/workflows", json={"name": "Empty", "steps": []})
        assert r.status_code == 422


def test_params_not_shared_between_steps():
    """Two steps with no params must each get their OWN dict — a shared
    mutable default would leak params across steps."""
    with TestClient(app) as client:
        wf = {
            "name": "Isolation",
            "steps": [
                {"name": "A", "tool": "search", "params": {"query": "x"}},
                {"name": "B", "tool": "parse", "params": {}},
            ],
        }
        run_res = client.post("/api/workflows/Isolation/run", json=wf)
        if run_res.status_code == 404:
            client.post("/api/workflows", json=wf)
            run_res = client.post("/api/workflows/Isolation/run").json()
        else:
            run_res = run_res.json()
        assert run_res["total_steps"] == 2
        # Step B ran with empty params -> parse used length default 0.
        assert "length 0" in run_res["logs"][1]["result"]