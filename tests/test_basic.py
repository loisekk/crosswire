import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_engine_loads():
    from adapters.engine import CrossPostEngine
    engine = CrossPostEngine("config/settings.example.json")
    assert engine is not None
    assert len(engine.targets) > 0
    assert len(engine.sources) > 0
    print(f"[OK] Engine loaded: {len(engine.targets)} targets, {len(engine.sources)} sources")


def test_ai_transformer():
    from adapters.ai_transformer import AITransformer, PLATFORM_PROMPTS
    assert len(PLATFORM_PROMPTS) == 14
    print(f"[OK] AI transformer: {len(PLATFORM_PROMPTS)} platform prompts defined")


def test_platform_adapters():
    from adapters import (
        DevToSourceAdapter, DevToTargetAdapter,
        HashnodeSourceAdapter, HashnodeTargetAdapter,
        LinkedInSourceAdapter, LinkedInTargetAdapter,
        XSourceAdapter, XTargetAdapter,
        RedditSourceAdapter, RedditTargetAdapter,
        IndeedTargetAdapter, NaukriTargetAdapter,
        MediumTargetAdapter,
        GlassdoorTargetAdapter, ZipRecruiterTargetAdapter,
        ShineTargetAdapter, TimesJobsTargetAdapter,
        ApnaTargetAdapter, IIMJobsTargetAdapter,
    )
    print("[OK] All 14 platform adapters imported successfully")


def test_dashboard():
    from dashboard.app import app
    assert app is not None
    print("[OK] Dashboard Flask app created")


def test_config():
    config_path = Path("config/settings.example.json")
    assert config_path.exists()
    with open(config_path) as f:
        config = json.load(f)
    assert "targets" in config
    assert "settings" in config
    print(f"[OK] Config valid: {len(config['targets'])} targets defined")


if __name__ == "__main__":
    print("\n=== Crosswire v2.0 Test Suite ===\n")
    test_engine_loads()
    test_ai_transformer()
    test_platform_adapters()
    test_dashboard()
    test_config()
    print("\n[PASS] All tests passed!\n")
