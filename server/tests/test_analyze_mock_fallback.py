from server.gemini_service import GeminiService


def test_analyze_returns_mock_when_no_api_key():
    # api_key_configured should be False in test environment; ensure mock response structure
    zones = [
        {"zone_id": "Gate A", "occupancy_rate": 95.0, "throughput_rate": 300.0},
        {"zone_id": "Gate B", "occupancy_rate": 30.0, "throughput_rate": 80.0},
    ]
    result = GeminiService.analyze_crowd(zones, threshold=80)
    assert 'alerts' in result
    assert 'instructions' in result
    assert isinstance(result['alerts'], list)
