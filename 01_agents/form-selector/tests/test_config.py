from form_selector.core.config import get_settings


def test_settings_defaults_and_overrides(monkeypatch):
    # Override a couple of envs
    monkeypatch.setenv("FORM_TEMPLATE_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("SUBMIT_API_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("ALLOWED_CORS_ORIGINS", "http://a.com,http://b.com")

    # clear lru_cache
    from form_selector.core.config import get_settings as _get, get_settings

    _get.cache_clear()  # type: ignore

    s = get_settings()
    assert s.FORM_TEMPLATE_BASE_URL == "http://localhost:8000"
    assert s.SUBMIT_API_BASE_URL == "http://localhost:8000"
    assert s.allowed_origins_list == ["http://a.com", "http://b.com"]
