from fastapi.testclient import TestClient
import pytest

from server.main import app

client = TestClient(app)

def test_root_health():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "online"

def test_crowd_zones():
    res = client.get("/api/crowd/zones")
    assert res.status_code == 200
    data = res.json()
    assert "zones" in data
    assert isinstance(data["zones"], list)
*** End Patch