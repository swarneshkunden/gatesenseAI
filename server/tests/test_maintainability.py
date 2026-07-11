import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


def test_core_modules_import_cleanly():
    modules = ["main", "config", "schemas", "routes.crowd", "routes.translation", "rate_limiter", "gemini_service"]
    for module_name in modules:
        assert importlib.import_module(module_name) is not None


def test_settings_defaults_are_safe():
    from config import settings
    assert settings.host in {"0.0.0.0", "127.0.0.1"}
    assert settings.rate_limit_default > 0
    assert settings.rate_limit_loose > 0
    assert settings.rate_limit_strict > 0


def test_validation_models_are_present():
    from schemas import TranslationRequest, ScriptRequest, CrowdStateUpdate
    assert TranslationRequest.__name__ == "TranslationRequest"
    assert ScriptRequest.__name__ == "ScriptRequest"
    assert CrowdStateUpdate.__name__ == "CrowdStateUpdate"
