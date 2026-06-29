from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_profile_matrix_eval.py"

spec = importlib.util.spec_from_file_location("run_profile_matrix_eval", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules["run_profile_matrix_eval"] = module
spec.loader.exec_module(module)


def test_profile_spec_requires_supported_api_profile_and_rejects_provider_alias() -> None:
    default = module.parse_profile_spec("current_hybrid:hybrid")
    assert default.key == "current_hybrid"
    assert default.api_profile == "hybrid"

    implicit_supported = module.parse_profile_spec("graph")
    assert implicit_supported.key == "graph"
    assert implicit_supported.api_profile == "graph"

    with pytest.raises(ValueError, match="bare profile specs"):
        module.parse_profile_spec("current_graph")

    with pytest.raises(ValueError, match="provider_profile is not executable"):
        module.parse_profile_spec("future_evo:none:evo_0_8b")

    with pytest.raises(ValueError, match="unsupported api_profile"):
        module.parse_profile_spec("candidate:evo_0_8b")


def test_safe_component_blocks_path_traversal() -> None:
    assert module.safe_component("temporal-order-001", "question id") == "temporal-order-001"
    for value in ("../escape", "nested/path", "bad..key", "", " leading"):
        with pytest.raises(ValueError):
            module.safe_component(value, "artifact")


def test_eval_body_overrides_runtime_and_uses_api_profile() -> None:
    payload = {"runtime": "hermes", "profile": "graph", "questions": []}
    profile = module.ProfileSpec(key="candidate", api_profile="hybrid")

    body = module.eval_body(payload, profile, "codex")

    assert body["runtime"] == "codex"
    assert body["profile"] == "hybrid"


def test_agent_context_body_uses_question_scope_and_profile() -> None:
    question = {
        "id": "q1",
        "query": "What changed?",
        "resource_ids": ["00000000-0000-0000-0000-000000000001"],
        "top_k": 5,
        "max_chars": 3000,
        "include_code_symbols": False,
    }
    profile = module.ProfileSpec(key="candidate", api_profile="hybrid")

    body = module.agent_context_body(question, profile, "hermes", 8000)

    assert body == {
        "query": "What changed?",
        "runtime": "hermes",
        "top_k": 5,
        "max_chars": 3000,
        "include_code_symbols": False,
        "resource_ids": ["00000000-0000-0000-0000-000000000001"],
        "profile": "hybrid",
    }


def test_hermes_grade_input_forbids_outside_knowledge_and_preserves_expectations() -> None:
    manifest = module.EvalManifestRef(
        key="temporal",
        path=Path("manifest.json"),
        manifest={"questions": []},
        digest="sha256:abc",
    )
    profile = module.ProfileSpec(key="candidate", api_profile="hybrid")
    question = {
        "id": "temporal-order-001",
        "query": "What happened first?",
        "required_texts": ["turn-001"],
        "temporal_assertion": {"evidence_markers": ["turn-001"], "requires_ordered_evidence": True},
    }

    grade_input = module.hermes_grade_input(
        manifest=manifest,
        profile=profile,
        question=question,
        retrieval_eval={"id": "temporal-order-001", "passed": True},
        agent_context={"citations": []},
        baseline_profile="static_embedding",
    )

    assert grade_input["schema_version"] == "sourcebrief.hermes-grade-input.v1"
    assert "Do not use outside knowledge" in grade_input["rubric"]["instruction"]
    assert grade_input["question"]["temporal_assertion"]["requires_ordered_evidence"] is True
    assert grade_input["baseline_profile"] == "static_embedding"
    assert grade_input["profile"]["api_profile"] == "hybrid"


def test_pairwise_grade_input_contains_blind_labels_and_identity_decode() -> None:
    manifest = module.EvalManifestRef(key="temporal", path=Path("manifest.json"), manifest={}, digest="sha256:abc")
    question = {"id": "q1", "query": "Compare"}
    baseline = module.ProfileSpec(key="static", api_profile="hybrid")
    candidate = module.ProfileSpec(key="evo_alias", api_profile="hybrid")

    grade_input, identity_decode = module.pairwise_grade_input(
        manifest=manifest,
        question=question,
        baseline_profile=baseline,
        candidate_profile=candidate,
        baseline_context={"context": "baseline"},
        candidate_context={"context": "candidate"},
    )

    assert grade_input["schema_version"] == "sourcebrief.hermes-pairwise-grade-input.v1"
    assert "profile" not in grade_input["A"]
    assert "profile" not in grade_input["B"]
    assert "identity_decode" not in grade_input
    assert identity_decode["schema_version"] == "sourcebrief.hermes-pairwise-identity-decode.v1"
    assert set(identity_decode) >= {"A", "B", "baseline", "candidate"}
    assert {identity_decode["A"]["key"], identity_decode["B"]["key"]} == {"static", "evo_alias"}
    assert identity_decode["baseline"]["key"] == "static"
    assert identity_decode["candidate"]["key"] == "evo_alias"
    assert "Do not pass to Hermes" in identity_decode["warning"]


def test_redaction_covers_bearer_cookie_and_session_tokens() -> None:
    raw = {
        "headers": {
            "Authorization": "Bearer abc.def.ghi",
            "Cookie": "sessionid=secret-cookie",
            "Set-Cookie": "auth=secret",
        },
        "message": "Authorization: Bearer tok_123 token=abc session_id=xyz",
    }

    redacted = module.redact(raw)

    assert "abc.def.ghi" not in str(redacted)
    assert "secret-cookie" not in str(redacted)
    assert "tok_123" not in redacted["message"]
    assert "session_id=<redacted>" in redacted["message"]


def test_run_matrix_overrides_eval_runtime_and_counts_preflight_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, dict | None]] = []

    class FakeClient:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def request(self, method: str, path: str, *, body: dict | None = None, expected: set[int] | None = None) -> dict:
            calls.append((method, path, body))
            if path == "/provider-health":
                raise RuntimeError("provider down")
            if path.endswith("/retrieval-profiles"):
                return {"default": "hybrid", "profiles": []}
            if path.endswith("/retrieval-evals"):
                assert body is not None
                assert body["runtime"] == "codex"
                assert body["profile"] == "hybrid"
                return {
                    "summary": {
                        "question_count": len(body["questions"]),
                        "passed_count": len(body["questions"]),
                        "failed_count": 0,
                        "pass_rate": 1.0,
                        "max_latency_ms": 1.0,
                        "failure_reasons": [],
                    },
                    "results": [
                        {"id": question["id"], "passed": True, "latency_ms": 1.0, "failure_reasons": []}
                        for question in body["questions"]
                    ],
                }
            raise AssertionError(f"unexpected request: {path}")

    monkeypatch.setattr(module, "ApiClient", FakeClient)
    out_dir = tmp_path / "matrix"
    args = SimpleNamespace(
        manifest=[f"temporal={ROOT / 'demo' / 'evo_temporal_50q' / 'eval_manifest.json'}"],
        profile=["candidate:hybrid"],
        profile_matrix=None,
        api_url="http://example.invalid",
        workspace_id="00000000-0000-0000-0000-000000000001",
        project_id="00000000-0000-0000-0000-000000000002",
        output_dir=str(out_dir),
        runtime="codex",
        email="demo@example.com",
        token=None,
        timeout=1.0,
        max_chars=8000,
        baseline_profile=None,
        skip_agent_context=True,
    )

    assert module.run_matrix(args) == 1
    aggregate = json.loads((out_dir / "aggregate-report.json").read_text())
    assert aggregate["preflight_errors"]
    assert aggregate["manifests"]["temporal"]["profiles"]["candidate"]["question_count"] == 50
    assert any(path.endswith("/retrieval-evals") and body and body["runtime"] == "codex" for _, path, body in calls)
