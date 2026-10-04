from fastapi.testclient import TestClient
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.db import models  # noqa (register tables)
from backend.app.main import app

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_ingestion_demo_mode():
    r = client.post("/api/v1/ingestion/run", json={"agency_external_id": "demo", "demo_rows": []})
    assert r.status_code == 200 and r.json()["mode"] == "DEMO/REPLAY"


def test_resources_list():
    for path in ["/agencies", "/routes", "/events", "/near-misses", "/patterns"]:
        r = client.get(f"/api/v1{path}")
        assert r.status_code == 200
