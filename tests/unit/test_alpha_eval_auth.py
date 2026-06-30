from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def load_alpha_eval():
    path = Path(__file__).resolve().parents[2] / "scripts" / "alpha_eval.py"
    spec = importlib.util.spec_from_file_location("alpha_eval_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clear_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in [
        "SOURCEBRIEF_QA_TOKEN",
        "CONTEXTSMITH_QA_TOKEN",
        "SOURCEBRIEF_TOKEN",
        "SOURCEBRIEF_ADMIN_EMAIL",
        "CONTEXTSMITH_ADMIN_EMAIL",
        "SOURCEBRIEF_ADMIN_PASSWORD",
        "CONTEXTSMITH_ADMIN_PASSWORD",
        "SOURCEBRIEF_DEV_AUTH",
        "CONTEXTSMITH_DEV_AUTH",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_alpha_eval_authenticates_with_admin_session(monkeypatch: pytest.MonkeyPatch) -> None:
    alpha_eval = load_alpha_eval()
    clear_auth_env(monkeypatch)
    monkeypatch.setenv("SOURCEBRIEF_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("SOURCEBRIEF_ADMIN_PASSWORD", "secret")

    calls = []

    def fake_post(url: str, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(status_code=200, text="", json=lambda: {"session_token": "session-token"})

    monkeypatch.setattr(alpha_eval.requests, "post", fake_post)

    alpha_eval.authenticate()

    assert alpha_eval.AUTH_MODE == "session"
    assert alpha_eval.HEADERS == {"Authorization": "Bearer session-token"}
    assert calls == [
        (
            f"{alpha_eval.BASE}/auth/login",
            {"json": {"email": "admin@example.com", "password": "secret"}, "timeout": 30},
        )
    ]
    assert alpha_eval.foreign_headers(123) == {"Authorization": "Bearer session-token"}


def test_alpha_eval_api_token_alone_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    alpha_eval = load_alpha_eval()
    clear_auth_env(monkeypatch)
    monkeypatch.setenv("SOURCEBRIEF_QA_TOKEN", "cs_test_token")

    with pytest.raises(SystemExit):
        alpha_eval.authenticate()

    assert alpha_eval.AUTH_MODE == ""
    assert alpha_eval.HEADERS == {}


def test_alpha_eval_admin_session_takes_precedence_over_api_token(monkeypatch: pytest.MonkeyPatch) -> None:
    alpha_eval = load_alpha_eval()
    clear_auth_env(monkeypatch)
    monkeypatch.setenv("SOURCEBRIEF_QA_TOKEN", "cs_test_token")
    monkeypatch.setenv("SOURCEBRIEF_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("SOURCEBRIEF_ADMIN_PASSWORD", "secret")

    monkeypatch.setattr(
        alpha_eval.requests,
        "post",
        lambda *args, **kwargs: SimpleNamespace(status_code=200, text="", json=lambda: {"session_token": "session-token"}),
    )

    alpha_eval.authenticate()

    assert alpha_eval.AUTH_MODE == "session"
    assert alpha_eval.HEADERS == {"Authorization": "Bearer session-token"}


def test_alpha_eval_dev_auth_is_explicit_and_uses_foreign_user(monkeypatch: pytest.MonkeyPatch) -> None:
    alpha_eval = load_alpha_eval()
    clear_auth_env(monkeypatch)
    monkeypatch.setenv("SOURCEBRIEF_DEV_AUTH", "true")

    alpha_eval.authenticate()

    assert alpha_eval.AUTH_MODE == "dev"
    assert alpha_eval.HEADERS == {"X-User-Email": alpha_eval.EMAIL}
    assert alpha_eval.foreign_headers(123) == {"X-User-Email": "foreign-alpha-eval-123@example.com"}


def test_alpha_eval_fails_closed_without_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    alpha_eval = load_alpha_eval()
    clear_auth_env(monkeypatch)
    monkeypatch.setenv("SOURCEBRIEF_DEV_AUTH", "false")

    with pytest.raises(SystemExit):
        alpha_eval.authenticate()

    assert alpha_eval.HEADERS == {}
    assert alpha_eval.AUTH_MODE == ""


def test_alpha_eval_main_authenticates_before_protected_requests(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    alpha_eval = load_alpha_eval()
    clear_auth_env(monkeypatch)
    calls: list[tuple[str, dict[str, str]]] = []

    dataset = tmp_path / "golden_questions.json"
    dataset.write_text("[]", encoding="utf-8")
    report = tmp_path / "alpha-report.json"
    monkeypatch.setattr(alpha_eval, "DATASET", dataset)
    monkeypatch.setenv("SOURCEBRIEF_ALPHA_EVAL_REPORT", str(report))

    def fake_authenticate() -> None:
        calls.append(("authenticate", {}))
        alpha_eval.HEADERS.clear()
        alpha_eval.HEADERS["Authorization"] = "Bearer session-token"
        alpha_eval.AUTH_MODE = "session"  # type: ignore[attr-defined]

    def fake_create_workspace_project(prefix: str, ts: int, headers=None):
        calls.append((f"create:{prefix}", dict(headers or alpha_eval.HEADERS)))
        return f"ws-{prefix}", f"project-{prefix}"

    monkeypatch.setattr(alpha_eval, "authenticate", fake_authenticate)
    monkeypatch.setattr(alpha_eval, "create_workspace_project", fake_create_workspace_project)
    monkeypatch.setattr(alpha_eval, "create_repo_resource", lambda *args, **kwargs: ("repo-resource", "repo-commit"))
    monkeypatch.setattr(alpha_eval, "create_markdown_resource", lambda *args, **kwargs: "markdown-resource")
    monkeypatch.setattr(alpha_eval, "evaluate_question", lambda *args, **kwargs: {"passed": True, "latency_ms": 1, "context_chars": 1})
    monkeypatch.setattr(alpha_eval, "assert_freshness", lambda *args, **kwargs: [])
    monkeypatch.setattr(alpha_eval, "assert_usage", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        alpha_eval,
        "assert_no_cross_tenant_leak",
        lambda *args, **kwargs: {"passed": True, "citation_count": 0, "context_chars": 0, "packet_item_count": 0},
    )

    alpha_eval.main()

    assert calls[0] == ("authenticate", {})
    assert calls[1][0] == "create:Alpha Eval"
    assert calls[1][1] == {"Authorization": "Bearer session-token"}
    assert calls[2][0] == "create:Foreign Alpha Eval"
    assert calls[2][1] == {"Authorization": "Bearer session-token"}
    assert report.exists()
