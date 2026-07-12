from fastapi.testclient import TestClient
import pytest

from server.main import app
from server.routes import translation
from server.gemini_service import GeminiService

client = TestClient(app)


def fake_translate(text, fan_lang, fan_origin, urgency, stress):
    return {
        "detected_language": "Spanish",
        "fan_text_en": "Where is the restroom?",
        "urgency_analysis": "Urgency: CASUAL, Stress: CALM. Standard informational request.",
        "suggested_response_en": "The nearest restroom is behind Gate C.",
        "suggested_response_fan_lang": "El baño más cercano está detrás de la Puerta C."
    }


def test_translate_endpoint_monkeypatch(monkeypatch):
    # Patch GeminiService.translate_query to our fake implementation
    monkeypatch.setattr(GeminiService, 'translate_query', staticmethod(fake_translate))

    payload = {
        "text": "¿Dónde está el baño?",
        "fan_language": "Spanish",
        "fan_origin": "Argentina",
        "urgency_level": "casual",
        "stress_level": "calm"
    }

    res = client.post("/api/translation/translate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "result" in data
    result = data["result"]
    assert result["detected_language"] == "Spanish"
    assert "restroom" in result["fan_text_en"].lower()
*** End Patch