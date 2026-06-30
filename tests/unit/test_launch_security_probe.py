from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def _load_probe_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "launch_security_probe.py"
    spec = importlib.util.spec_from_file_location("launch_security_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["launch_security_probe"] = module
    spec.loader.exec_module(module)
    return module


def test_launch_security_probe_redacts_tokens_secrets_and_local_paths() -> None:
    probe = _load_probe_module()

    raw = "token=cs_abc1234567890SECRET password=hunter2 path=/home/user/private/file.md Bearer abc.def"
    redacted = probe.redact_text(raw)

    assert "cs_abc" not in redacted
    assert "hunter2" not in redacted
    assert "/home/user" not in redacted
    assert "Bearer abc.def" not in redacted
    assert redacted.count("***REDACTED***") >= 4


def test_launch_security_probe_public_artifact_scan_and_status() -> None:
    probe = _load_probe_module()

    unsafe = {
        "token": "cs_abc1234567890SECRET",
        "path": "/tmp/sourcebrief-secret.txt",
        "id": "11111111-1111-1111-1111-111111111111",
    }
    counts = probe.scan_public_artifact(unsafe)

    assert counts["token_like"] == 1
    assert counts["local_path"] == 1
    assert counts["raw_uuid"] == 1
    assert probe.status_from_counts(counts) == "block"
    assert probe.status_from_counts({"token_like": 0, "local_path": 0, "raw_uuid": 1}, allow_raw_uuid=True) == "pass"


def test_launch_security_probe_timeout_output_handles_bytes(monkeypatch, tmp_path: Path) -> None:
    probe = _load_probe_module()

    def fake_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise subprocess.TimeoutExpired(cmd=["fake"], timeout=1, output=b"token=cs_abc1234567890", stderr=b"/home/me/file")

    monkeypatch.setattr(probe.subprocess, "run", fake_run)

    result = probe.run_command(["fake"], cwd=tmp_path, timeout=1)

    assert result["exit_code"] == 124
    assert "cs_abc" not in result["stdout"]
    assert "/home/me" not in result["stderr"]
    assert "***REDACTED***" in result["stdout"]
    assert "***REDACTED***" in result["stderr"]


def test_launch_security_probe_redacts_json_secret_keys_and_scans_json_shapes() -> None:
    probe = _load_probe_module()

    raw = {"provider_health": {"api_key": "plain-secret-value", "client_secret": "plain-client-secret"}}

    assert probe.scan_public_artifact(raw)["secret_assignment"] >= 2
    redacted = probe.redact_json(raw)
    assert redacted["provider_health"]["api_key"] == "***REDACTED***"
    assert redacted["provider_health"]["client_secret"] == "***REDACTED***"
    assert "plain-secret" not in str(redacted)
    assert probe.scan_public_artifact(redacted)["secret_assignment"] == 0


def test_launch_security_probe_marker_check_ignores_echoed_query() -> None:
    probe = _load_probe_module()

    echoed_only = {
        "query": probe.MARKER,
        "answer": "Unrelated answer",
        "citations": [{"resource_id": "res-a", "snippet": "unrelated content"}],
    }
    evidence_hit = {
        "query": probe.MARKER,
        "answer": "The cited context contains the marker.",
        "citations": [{"resource_id": "res-a", "snippet": f"Evidence has {probe.MARKER}."}],
    }

    assert not probe.response_contains_marker_evidence(echoed_only, probe.MARKER)
    assert probe.response_contains_marker_evidence(evidence_hit, probe.MARKER)


def test_launch_security_probe_false_premise_requires_explicit_caveat() -> None:
    probe = _load_probe_module()

    answered_with_one_citation = {"answer": "The imaginary deployment used optimizer v2.", "citations": [{"resource_id": "res-a"}]}
    caveated = {"answer": "There is insufficient evidence in the cited context to answer.", "citations": [{"resource_id": "res-a"}]}

    assert not probe.false_premise_is_handled(answered_with_one_citation)
    assert probe.false_premise_is_handled(caveated)


def test_launch_security_probe_browser_transcript_checks_failures_not_only_redaction() -> None:
    probe = _load_probe_module()

    failure_json = '{"console":[{"type":"error","text":"boom"}],"pageErrors":["crash"],"failedRequests":[{"url":"/api"}],"badResponses":[{"status":500}]}'
    clean_json = '{"console":[],"pageErrors":[],"failedRequests":[],"badResponses":[]}'
    failure_text = "console.error: Failed to fetch network status 500"

    assert probe.analyze_browser_transcript(failure_json)["status"] == "block"
    assert probe.analyze_browser_transcript(failure_text)["status"] == "block"
    assert probe.analyze_browser_transcript(clean_json)["status"] == "pass"


def test_launch_security_probe_risk_exit_is_fail_closed_by_default(monkeypatch, tmp_path: Path) -> None:
    probe = _load_probe_module()

    def fake_run_probe(args):  # noqa: ANN001
        return {"run_id": "risk-run", "status": "risk", "checks": {}}

    monkeypatch.setattr(probe, "run_probe", fake_run_probe)

    output = tmp_path / "probe.json"
    assert probe.main(["--output", str(output)]) == 1
    assert probe.main(["--output", str(output), "--allow-risk-exit-zero"]) == 0


def test_launch_security_probe_make_target_does_not_enable_dev_auth_by_default() -> None:
    makefile = (Path(__file__).resolve().parents[2] / "Makefile").read_text()
    target = makefile.split("launch-security-probe:", 1)[1].split("\n\n", 1)[0]

    assert "SOURCEBRIEF_DEV_AUTH=true" not in target
    assert "--dev-auth-email" not in target
    assert "--email" in target
    assert "LAUNCH_SECURITY_BROWSER_TRANSCRIPT" in target
