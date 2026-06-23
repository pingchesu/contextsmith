from sourcebrief_api.main import _cors_origins


def test_default_cors_origins_include_packaged_dev_and_e2e_web_ports(monkeypatch):
    monkeypatch.delenv("SOURCEBRIEF_CORS_ORIGINS", raising=False)
    monkeypatch.delenv("CONTEXTSMITH_CORS_ORIGINS", raising=False)

    origins = _cors_origins()

    assert "http://localhost:13000" in origins
    assert "http://localhost:3000" in origins
    assert "http://localhost:3105" in origins
    assert "http://localhost:3205" in origins
    assert "http://127.0.0.1:3205" in origins


def test_explicit_cors_origins_override_defaults(monkeypatch):
    monkeypatch.setenv("SOURCEBRIEF_CORS_ORIGINS", "https://app.example.com, http://localhost:9999")

    assert _cors_origins() == ["https://app.example.com", "http://localhost:9999"]
