#!/usr/bin/env python3
"""Collect SourceBrief launch security/observability/failure-mode evidence.

This probe is intentionally live-service oriented. It creates a tiny disposable
workspace/project/resource set, mints scoped API tokens, proves allowed and denied
paths, captures observability snapshots, and writes a redacted JSON report.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

TOKEN_RE = re.compile(r"(cs_[A-Za-z0-9_-]{8,}|Bearer\s+[A-Za-z0-9._-]+|gh[pousr]_[A-Za-z0-9_]+)")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?P<prefix>\b(?:token|api[_-]?key|secret|password|session[_-]?token|client[_-]?secret)\b\s*[:=]\s*)(?P<quote>[\"']?)(?P<value>[^\s,;\"']+)(?P=quote)",
    re.IGNORECASE,
)
LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])(?:/home/[^\s\"']+|/tmp/[^\s\"']+|file://[^\s\"']+)")
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)
REDACTED = "***REDACTED***"
MARKER = "launchsecuritymarker"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def redact_text(text: str) -> str:
    def replace_assignment(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{match.group('quote')}{REDACTED}{match.group('quote')}"

    text = SECRET_ASSIGNMENT_RE.sub(replace_assignment, text)
    text = TOKEN_RE.sub(REDACTED, text)
    text = LOCAL_PATH_RE.sub(REDACTED, text)
    return text


def redact_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): redact_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_json(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def scan_public_artifact(value: Any) -> dict[str, Any]:
    """Return counts for patterns that should not appear in public artifacts."""
    text = json.dumps(value, sort_keys=True, default=str) if not isinstance(value, str) else value
    return {
        "token_like": len(TOKEN_RE.findall(text)),
        "secret_assignment": len(SECRET_ASSIGNMENT_RE.findall(text)),
        "local_path": len(LOCAL_PATH_RE.findall(text)),
        "raw_uuid": len(UUID_RE.findall(text)),
    }


def status_from_counts(counts: dict[str, int], *, allow_raw_uuid: bool = False) -> str:
    failures = {
        key: count
        for key, count in counts.items()
        if count and not (allow_raw_uuid and key == "raw_uuid")
    }
    return "pass" if not failures else "block"


@dataclass
class Api:
    base_url: str
    headers: dict[str, str]

    def request(self, method: str, path: str, *, expected: set[int] | int, **kwargs: Any) -> requests.Response:
        expected_set = {expected} if isinstance(expected, int) else set(expected)
        response = requests.request(method, f"{self.base_url}{path}", headers=self.headers, timeout=20, **kwargs)
        if response.status_code not in expected_set:
            raise RuntimeError(
                f"{method} {path} expected {sorted(expected_set)}, got {response.status_code}: {redact_text(response.text[:500])}"
            )
        return response

    def json(self, method: str, path: str, *, expected: set[int] | int, **kwargs: Any) -> Any:
        response = self.request(method, path, expected=expected, **kwargs)
        return response.json() if response.content else None


def make_auth_headers(args: argparse.Namespace) -> tuple[dict[str, str], dict[str, Any]]:
    token = os.getenv(args.token_env) if args.token_env else None
    if token:
        return {"Authorization": f"Bearer {token}"}, {"mode": "token_env", "token_env": args.token_env}

    password = os.getenv(args.password_env) if args.password_env else None
    if args.email and password:
        response = requests.post(
            f"{args.api_url.rstrip('/')}/auth/login",
            json={"email": args.email, "password": password},
            timeout=20,
        )
        if response.status_code != 200:
            raise RuntimeError(f"admin/session login failed with HTTP {response.status_code}: {redact_text(response.text[:300])}")
        session_token = response.json().get("session_token")
        if not session_token:
            raise RuntimeError("login response did not include session_token")
        return {"Authorization": f"Bearer {session_token}"}, {"mode": "session_login", "email": args.email}

    if args.dev_auth_email:
        return {"X-User-Email": args.dev_auth_email}, {"mode": "dev_auth_email", "email": args.dev_auth_email}

    raise RuntimeError("provide --token-env, --email with --password-env, or --dev-auth-email")


def create_markdown_resource(api: Api, ws: str, project: str, *, name: str, marker: str) -> str:
    resource = api.json(
        "POST",
        f"/workspaces/{ws}/projects/{project}/resources",
        expected=201,
        json={
            "type": "markdown",
            "name": name,
            "uri": f"doc://{name.lower().replace(' ', '-')}",
            "source_config": {"content": f"# {name}\n\nThe {marker} evidence marker belongs only to {name}.\n"},
        },
    )
    return str(resource["id"])


def wait_for_index(api: Api, ws: str, run_id: str, *, timeout: int = 90) -> dict[str, Any]:
    deadline = time.time() + timeout
    current: dict[str, Any] = {"status": "queued"}
    while time.time() < deadline:
        current = api.json("GET", f"/workspaces/{ws}/index-runs/{run_id}", expected=200)
        if current.get("status") in {"succeeded", "failed"}:
            break
        time.sleep(2)
    if current.get("status") != "succeeded":
        raise RuntimeError(f"index run did not succeed: {redact_text(json.dumps(current, default=str))}")
    return current


def refresh_resource(api: Api, ws: str, project: str, resource_id: str) -> dict[str, Any]:
    run = api.json("POST", f"/workspaces/{ws}/projects/{project}/resources/{resource_id}/refresh", expected=202)
    return wait_for_index(api, ws, str(run["id"]))


def create_runtime_token(api: Api, ws: str, project: str, resource_id: str) -> tuple[str, str]:
    created = api.json(
        "POST",
        f"/workspaces/{ws}/api-tokens",
        expected=201,
        json={
            "name": "launch-security-probe-context-token",
            "scopes": ["project:read", "project:query", "resource:read", "review:read"],
            "allowed_project_ids": [project],
            "allowed_resource_ids": [resource_id],
        },
    )
    token = created.get("token")
    if not token:
        raise RuntimeError("token create did not return one-time plaintext token")
    if "token" in created.get("api_token", {}):
        raise RuntimeError("api_token metadata leaked plaintext token")
    token_id = created.get("api_token", {}).get("id")
    if not token_id:
        raise RuntimeError("token create did not return token metadata id")
    return str(token), str(token_id)


def run_command(command: list[str], *, cwd: Path, timeout: int = 60) -> dict[str, Any]:
    started = utc_now()
    try:
        result = subprocess.run(command, cwd=cwd, timeout=timeout, text=True, capture_output=True, check=False)
        return {
            "command": command,
            "started_at": started,
            "exit_code": result.returncode,
            "stdout": redact_text(result.stdout[-4000:]),
            "stderr": redact_text(result.stderr[-4000:]),
        }
    except FileNotFoundError as exc:
        return {"command": command, "started_at": started, "exit_code": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "command": command,
            "started_at": started,
            "exit_code": 124,
            "stdout": redact_text(stdout[-4000:]),
            "stderr": redact_text((stderr or f"timeout after {timeout}s")[-4000:]),
        }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    root = Path.cwd()
    api_url = args.api_url.rstrip("/")
    headers, auth = make_auth_headers(args)
    admin_api = Api(api_url, headers)
    run_id = args.run_id or f"launch-security-{utc_now().replace(':', '').replace('-', '')}"
    checks: dict[str, Any] = {}

    invalid_login = requests.post(
        f"{api_url}/auth/login",
        json={"email": args.email or "invalid@example.com", "password": "sourcebrief-invalid-password"},
        timeout=20,
    )
    checks["invalid_login"] = {"status": "pass" if invalid_login.status_code == 401 else "block", "http_status": invalid_login.status_code}

    provider_health = requests.get(f"{api_url}/provider-health", timeout=20)
    checks["provider_health"] = {
        "status": "pass" if provider_health.status_code == 200 else "block",
        "http_status": provider_health.status_code,
        "body": redact_json(provider_health.json() if provider_health.content else {}),
    }

    workspace = admin_api.json("POST", "/workspaces", expected=201, json={"name": "Launch Security", "slug": f"launch-security-{int(time.time())}"})
    ws = str(workspace["id"])
    project_a = admin_api.json("POST", f"/workspaces/{ws}/projects", expected=201, json={"name": "Allowed Project", "description": "launch security allowed"})
    project_b = admin_api.json("POST", f"/workspaces/{ws}/projects", expected=201, json={"name": "Denied Project", "description": "launch security denied"})
    proj_a = str(project_a["id"])
    proj_b = str(project_b["id"])
    res_a = create_markdown_resource(admin_api, ws, proj_a, name="Allowed Runbook", marker=MARKER)
    res_b = create_markdown_resource(admin_api, ws, proj_a, name="Denied Runbook", marker="deniedmarker")
    res_other_project = create_markdown_resource(admin_api, ws, proj_b, name="Other Project Runbook", marker="otherprojectmarker")

    index_runs = {
        "allowed": refresh_resource(admin_api, ws, proj_a, res_a),
        "denied_same_project": refresh_resource(admin_api, ws, proj_a, res_b),
        "denied_other_project": refresh_resource(admin_api, ws, proj_b, res_other_project),
    }
    checks["queue_index_runs"] = {
        "status": "pass" if all(run.get("status") == "succeeded" for run in index_runs.values()) else "block",
        "runs": redact_json(index_runs),
    }

    restricted_token, restricted_token_id = create_runtime_token(admin_api, ws, proj_a, res_a)
    restricted_api = Api(api_url, {"Authorization": f"Bearer {restricted_token}"})

    allowed_context = restricted_api.json(
        "POST",
        f"/workspaces/{ws}/projects/{proj_a}/agent-context",
        expected=200,
        json={"query": MARKER, "resource_ids": [res_a], "runtime": "hermes", "include_answer": True},
    )
    allowed_citations = allowed_context.get("citations") or []
    allowed_ok = MARKER in json.dumps(allowed_context).lower() and allowed_citations and all(str(c.get("resource_id")) == res_a for c in allowed_citations)
    checks["scoped_token_allowed_context"] = {
        "status": "pass" if allowed_ok else "block",
        "citation_count": len(allowed_citations),
        "resource_ids": sorted({str(c.get("resource_id")) for c in allowed_citations}),
    }

    denied_project = restricted_api.request(
        "POST",
        f"/workspaces/{ws}/projects/{proj_b}/agent-context",
        expected={403, 404},
        json={"query": "otherprojectmarker", "resource_ids": [res_other_project]},
    )
    checks["cross_project_denial"] = {"status": "pass", "http_status": denied_project.status_code}

    denied_resource = restricted_api.request(
        "POST",
        f"/workspaces/{ws}/projects/{proj_a}/agent-context",
        expected={403, 404},
        json={"query": "deniedmarker", "resource_ids": [res_b]},
    )
    checks["cross_resource_denial"] = {"status": "pass", "http_status": denied_resource.status_code}

    missing_scope_created = admin_api.json(
        "POST",
        f"/workspaces/{ws}/api-tokens",
        expected=201,
        json={
            "name": "launch-security-probe-readonly-token",
            "scopes": ["project:read", "resource:read"],
            "allowed_project_ids": [proj_a],
            "allowed_resource_ids": [res_a],
        },
    )
    missing_scope_token = str(missing_scope_created["token"])
    missing_scope_token_id = str(missing_scope_created["api_token"]["id"])
    missing_scope_response = Api(api_url, {"Authorization": f"Bearer {missing_scope_token}"}).request(
        "POST",
        f"/workspaces/{ws}/projects/{proj_a}/agent-context",
        expected=403,
        json={"query": MARKER, "resource_ids": [res_a]},
    )
    checks["scope_mismatch_denial"] = {"status": "pass", "http_status": missing_scope_response.status_code}

    mcp_denial = restricted_api.request(
        "POST",
        f"/mcp/{ws}/{proj_b}",
        expected={403, 404},
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "launch-security-probe", "version": "1"}}},
    )
    checks["mcp_project_scope_denial"] = {"status": "pass", "http_status": mcp_denial.status_code}

    false_premise = restricted_api.json(
        "POST",
        f"/workspaces/{ws}/projects/{proj_a}/agent-context",
        expected=200,
        json={"query": "Which deployment used the imaginary no-such-sourcebrief-launch-fact?", "resource_ids": [res_a], "runtime": "hermes", "include_answer": True},
    )
    false_context = json.dumps(false_premise).lower()
    checks["false_premise_behavior"] = {
        "status": "pass" if "insufficient" in false_context or "not enough" in false_context or len(false_premise.get("citations") or []) <= 1 else "risk",
        "citation_count": len(false_premise.get("citations") or []),
        "answer_excerpt": redact_text(str(false_premise.get("answer") or ""))[:600],
    }

    empty_project = admin_api.json("POST", f"/workspaces/{ws}/projects", expected=201, json={"name": "No Snapshot Project"})
    empty_response = admin_api.json(
        "POST",
        f"/workspaces/{ws}/projects/{empty_project['id']}/agent-context",
        expected=200,
        json={"query": "anything", "runtime": "hermes", "include_answer": True},
    )
    checks["no_source_no_snapshot"] = {
        "status": "pass" if len(empty_response.get("citations") or []) == 0 else "block",
        "citation_count": len(empty_response.get("citations") or []),
        "answer_excerpt": redact_text(str(empty_response.get("answer") or ""))[:600],
    }

    failed_import = admin_api.request(
        "POST",
        f"/workspaces/{ws}/projects/{proj_a}/resources",
        expected=422,
        json={"type": "upload", "name": "Bad Upload", "uri": "upload://bad", "source_config": {"path": "/home/user/secret.md"}},
    )
    checks["failed_or_partial_import"] = {"status": "pass", "http_status": failed_import.status_code}

    revoked_tokens: dict[str, bool] = {}
    for label, token_id in {
        "runtime_context": restricted_token_id,
        "missing_scope": missing_scope_token_id,
    }.items():
        revoked = admin_api.json("DELETE", f"/workspaces/{ws}/api-tokens/{token_id}", expected=200)
        revoked_tokens[label] = bool(revoked.get("revoked_at"))
    checks["token_revocation"] = {
        "status": "pass" if all(revoked_tokens.values()) else "block",
        "revoked": revoked_tokens,
    }

    audits = admin_api.json("GET", f"/workspaces/{ws}/audit-events", expected=200)
    audit_actions = [event.get("action") for event in audits[:20]]
    checks["audit_events"] = {
        "status": "pass" if {"workspace.create", "project.create", "api_token.create"}.issubset(set(audit_actions)) else "risk",
        "recent_actions": audit_actions[:20],
    }

    logs: dict[str, Any]
    if args.compose_project_name:
        logs = {
            "api": run_command(["docker", "compose", "-p", args.compose_project_name, "logs", "--tail", "120", "api"], cwd=root),
            "worker_default": run_command(["docker", "compose", "-p", args.compose_project_name, "logs", "--tail", "120", "worker-default"], cwd=root),
            "worker_maintenance": run_command(["docker", "compose", "-p", args.compose_project_name, "logs", "--tail", "120", "worker-maintenance"], cwd=root),
        }
        log_status = "pass" if any(item.get("exit_code") == 0 for item in logs.values()) else "risk"
    else:
        logs = {"omitted_reason": "--compose-project-name not provided; server-side API/index/audit/provider evidence captured instead"}
        log_status = "risk"
    checks["service_logs"] = {"status": log_status, "logs": logs}

    if args.browser_transcript:
        transcript_path = Path(args.browser_transcript)
        transcript_text = transcript_path.read_text(encoding="utf-8")
        transcript_scan = scan_public_artifact(transcript_text)
        checks["browser_console_network"] = {
            "status": status_from_counts(transcript_scan),
            "source": str(transcript_path),
            "redaction_scan": transcript_scan,
        }
    else:
        checks["browser_console_network"] = {
            "status": "risk",
            "omitted_reason": "browser console/network transcript not supplied; #210/#213 browser proof must provide it before launch PASS",
        }

    report = {
        "schema": "sourcebrief.launch_security_probe.v1",
        "run_id": run_id,
        "captured_at": utc_now(),
        "candidate": {
            "git_head": run_command(["git", "rev-parse", "HEAD"], cwd=root).get("stdout", "").strip(),
            "git_status": run_command(["git", "status", "--short", "--branch"], cwd=root),
        },
        "api_url": api_url,
        "web_url": args.web_url.rstrip("/"),
        "auth": auth,
        "workspace": {"id": ws, "name": workspace.get("name")},
        "projects": {"allowed": proj_a, "denied": proj_b, "empty": str(empty_project["id"])},
        "resources": {"allowed": res_a, "denied_same_project": res_b, "denied_other_project": res_other_project},
        "checks": checks,
    }
    public_scan = scan_public_artifact(redact_json(report))
    checks["public_artifact_redaction"] = {
        "status": status_from_counts(public_scan, allow_raw_uuid=True),
        "redaction_scan_after_redaction": public_scan,
        "raw_uuid_policy": "allowed only in this ignored internal manifest; public committed excerpts must normalize IDs",
    }
    statuses = [check.get("status") for check in checks.values() if isinstance(check, dict)]
    report["status"] = "block" if "block" in statuses else ("risk" if "risk" in statuses else "pass")
    report["checks"] = checks
    return redact_json(report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect SourceBrief launch security/failure-mode evidence from a live local stack.")
    parser.add_argument("--api-url", default=os.getenv("SOURCEBRIEF_API_URL") or os.getenv("API_URL") or "http://localhost:18000")
    parser.add_argument("--web-url", default=os.getenv("SOURCEBRIEF_WEB_URL") or os.getenv("WEB_URL") or "http://localhost:13000")
    parser.add_argument("--email", default=os.getenv("SOURCEBRIEF_ADMIN_EMAIL"))
    parser.add_argument("--password-env", default="SOURCEBRIEF_ADMIN_PASSWORD")
    parser.add_argument("--token-env", help="environment variable containing an existing admin/session token")
    parser.add_argument("--dev-auth-email", help="use local dev-auth X-User-Email instead of token/session login")
    parser.add_argument("--compose-project-name", default=os.getenv("COMPOSE_PROJECT_NAME"), help="capture docker compose logs for this project")
    parser.add_argument("--browser-transcript", help="optional browser console/network transcript JSON/text captured by #210/#213")
    parser.add_argument("--run-id")
    parser.add_argument("--output", help="output JSON path; defaults to artifacts/e2e/<run-id>/launch-security-probe.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_probe(args)
    except Exception as exc:
        print(f"launch security probe failed: {redact_text(str(exc))}", file=sys.stderr)
        return 1
    output = Path(args.output) if args.output else Path("artifacts") / "e2e" / str(report["run_id"]) / "launch-security-probe.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output)}, sort_keys=True))
    return 0 if report["status"] in {"pass", "risk"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
