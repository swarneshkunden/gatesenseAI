from fastapi.testclient import TestClient
from server.main import app
from server.gemini_service import GeminiService

client = TestClient(app)


def fake_broadcast(scenario, target_gates, languages):
    return {
        "scenario": scenario,
        "broadcast_scripts": {lang: f"Fake script for {lang}" for lang in languages}
    }


def test_generate_broadcast(monkeypatch):
    monkeypatch.setattr(GeminiService, 'generate_broadcast', staticmethod(fake_broadcast))

    payload = {
        "scenario": "Test scenario",
        "target_gates": ["Gate A"],
        "languages": ["Spanish", "French"]
    }

    res = client.post('/api/translation/broadcast-script', json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data['status'] == 'success'
    result = data['result']
    assert 'broadcast_scripts' in result
    assert 'Spanish' in result['broadcast_scripts']
