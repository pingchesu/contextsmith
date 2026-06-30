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
