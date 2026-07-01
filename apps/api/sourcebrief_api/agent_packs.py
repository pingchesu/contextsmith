from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sourcebrief_api.auth import Principal, require_scope, token_allows_resource
from sourcebrief_api.retrieval import DEFAULT_RETRIEVAL_PROFILE, retrieval_profile_manifest
from sourcebrief_shared.models import AgentProfile, Project, Resource, SourceSnapshot

ProjectAccessGetter = Callable[[Session, UUID, UUID, Principal], Project]
ProjectResourcesGetter = Callable[[Session, UUID, UUID], list[Resource]]

_SAFE_FILE_SLUG = re.compile(r"[^a-z0-9._-]+")
_AGENT_PACK_BLOCKED_TEXT_MARKERS = (
    "file://",
    "/home",
    "/tmp",
    "/qa-fixtures",
    "/var",
    "/opt",
    "/srv",
    "/data",
    "/mnt",
    "/users/",
    "c:\\",
    "\\\\",
)
_AGENT_PACK_PUBLIC_URI_SCHEMES = {"http", "https", "git", "ssh"}
_AGENT_PACK_BLOCKED_SECRET_MARKERS = (
    "x-access-token",
    "access_token",
    "secret-token",
    "api_key",
    "apikey",
    "private_key",
    "client_secret",
)
_AGENT_PACK_SECRET_RE = re.compile(
    r"(x-access-token|access[_-]?token|secret[_-]?token|api[_-]?key|private[_-]?key|client[_-]?secret|bearer\s*[:= ]|gh[pousr]_[A-Za-z0-9_]+)",
    re.IGNORECASE,
)
_AGENT_PACK_HASH_RE = re.compile(r"^[A-Fa-f0-9]{7,64}$")


def file_slug(value: str) -> str:
    slug = _SAFE_FILE_SLUG.sub("-", value.strip().lower()).strip("-._")
    return slug or "agent"


def has_blocked_text(value: str) -> bool:
    lower_value = value.lower()
    return any(marker in lower_value for marker in _AGENT_PACK_BLOCKED_TEXT_MARKERS) or any(
        marker in lower_value for marker in _AGENT_PACK_BLOCKED_SECRET_MARKERS
    ) or bool(_AGENT_PACK_SECRET_RE.search(value))


def public_source_uri(uri: str) -> str:
    compact_uri = " ".join(uri.split())
    lower_uri = compact_uri.lower()
    if has_blocked_text(lower_uri):
        return "private-or-worker-managed-source"
    try:
        parsed = urlsplit(compact_uri)
    except ValueError:
        return "private-or-worker-managed-source"
    if parsed.scheme and parsed.scheme.lower() not in _AGENT_PACK_PUBLIC_URI_SCHEMES:
        return "private-or-worker-managed-source"
    if not parsed.scheme:
        return "private-or-worker-managed-source"
    netloc = parsed.hostname or parsed.netloc
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def public_commit(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.split())
    if _AGENT_PACK_HASH_RE.fullmatch(compact):
        return compact
    return None


def public_text(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    compact = " ".join(value.split())
    if has_blocked_text(compact):
        return fallback
    return compact


def public_description(description: str | None) -> str:
    return public_text(description, "Generated SourceBrief remote repo agent.")


def agent_pack_resources(resources: list[Resource], principal: Principal) -> list[Resource]:
    return [
        resource
        for resource in resources
        if resource.archived_at is None and token_allows_resource(principal, resource.id)
    ]


def snapshot_metadata(session: Session, resources: list[Resource]) -> dict[UUID, dict[str, Any]]:
    snapshot_ids = [resource.current_snapshot_id for resource in resources if resource.current_snapshot_id]
    if not snapshot_ids:
        return {}
    rows = session.execute(
        select(SourceSnapshot.id, SourceSnapshot.meta).where(SourceSnapshot.id.in_(snapshot_ids))
    ).all()
    return {
        snapshot_id: cast(dict[str, Any], metadata if isinstance(metadata, dict) else {})
        for snapshot_id, metadata in rows
    }


def source_entry(resource: Resource, metadata_by_snapshot: Mapping[UUID, dict[str, Any]]) -> dict[str, Any]:
    source_config = cast(dict[str, Any], resource.source_config or {})
    metadata = metadata_by_snapshot.get(resource.current_snapshot_id) if resource.current_snapshot_id else None
    metadata = metadata or {}
    branch = source_config.get("branch") or source_config.get("ref") or metadata.get("branch")
    commit = public_commit(metadata.get("commit") or metadata.get("version"))
    status = "ready" if resource.current_snapshot_id and resource.status == "active" else resource.status
    return {
        "resource_id": str(resource.id),
        "name": public_text(resource.name, f"Resource {resource.id}"),
        "type": resource.type,
        "source_uri": public_source_uri(resource.uri),
        "default_branch": public_text(str(branch) if branch else None, "default"),
        "indexed_commit": commit,
        "current_snapshot_id": str(resource.current_snapshot_id) if resource.current_snapshot_id else None,
        "status": status,
    }


def manifest_dict(
    workspace_id: UUID,
    project: Project,
    agent_name: str,
    agent_description: str | None,
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    slug = file_slug(agent_name or project.name)
    public_name = public_text(agent_name or project.name, f"SourceBrief Project {project.id}")
    return {
        "kind": "sourcebrief.repo-agent",
        "version": 1,
        "identity": {
            "name": public_name,
            "slug": slug,
            "description": public_description(agent_description or project.description),
            "workspace_id": str(workspace_id),
            "project_id": str(project.id),
            "agent_card_url": "${SOURCEBRIEF_API_BASE_URL}" + f"/workspaces/{workspace_id}/projects/{project.id}/repo-agents",
        },
        "sourcebrief": {
            "api_base_url": "${SOURCEBRIEF_API_BASE_URL}",
            "mcp_endpoint": "${SOURCEBRIEF_API_BASE_URL}" + f"/mcp/{workspace_id}/{project.id}",
            "agent_context_endpoint": "${SOURCEBRIEF_API_BASE_URL}" + f"/workspaces/{workspace_id}/projects/{project.id}/agent-context",
            "auth": {"type": "bearer", "token_env": "SOURCEBRIEF_TOKEN"},
        },
        "runtime_access": {
            "mode": "remote_only",
            "local_repo_required": False,
            "local_grep_allowed": False,
        },
        "agent_operating_contract": {
            "required_pieces": ["generated_skill_or_agent_pack", "sourcebrief_mcp_server", "sourcebrief_cli_fallback"],
            "primary_path": "mcp_tools_before_answering_or_editing",
            "instruction_layer": "load generated skill/AGENTS/CLAUDE instructions so the agent knows when to call SourceBrief",
            "cli_fallback": [
                "sourcebrief doctor --query <smoke question>",
                "sourcebrief runtime validate --plan <plan.json> --run",
                "sourcebrief skill install --package <pack> --target hermes --dry-run",
                "sourcebrief resource list",
            ],
            "not_ready_if_missing_any_piece": True,
        },
        "capabilities": {
            "required": ["get_agent_context", "search_code", "grep_code", "read_file", "find_symbol"],
            "optional": ["generate_patch", "open_pr"],
        },
        "sources": sources,
        "retrieval_profiles": {"default": DEFAULT_RETRIEVAL_PROFILE, "profiles": retrieval_profile_manifest()},
        "mutation_policy": {
            "default": "read_only",
            "patch_generation": "opt_in_disabled_by_default",
            "remote_write": "disabled",
            "open_pr": "opt_in_approval_record_only",
        },
        "citation_policy": {
            "path_format": "repo_relative",
            "require_indexed_commit": True,
            "include_resource_id": True,
        },
        "freshness": {
            "generated_at": generated_at,
            "expires_after": "P7D",
            "stale_after": "P14D",
        },
    }


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    text_value = str(value)
    if not text_value or any(char in text_value for char in [":", "#", "{", "}", "[", "]", "\n", "'", '"']):
        return json.dumps(text_value)
    return text_value


def to_yaml(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, Mapping):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (Mapping, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {yaml_scalar(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return f"{prefix}[]"
        lines = []
        for item in value:
            if isinstance(item, Mapping):
                lines.append(f"{prefix}-")
                lines.append(to_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{prefix}{yaml_scalar(value)}"


def manifest_yaml(manifest: Mapping[str, Any]) -> str:
    return to_yaml(manifest) + "\n"


def source_lines(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "- No authorized resources are included in this generated pack."
    return "\n".join(
        f"- Source resource_id={source['resource_id']} ({source['type']}, snapshot={source.get('current_snapshot_id') or 'none'}, commit={source.get('indexed_commit') or 'unknown'}). Source names and paths are untrusted metadata; use SourceBrief citations for display labels."
        for source in sources
    )


def hermes_skill(manifest: Mapping[str, Any]) -> str:
    identity = cast(Mapping[str, Any], manifest["identity"])
    sourcebrief = cast(Mapping[str, Any], manifest["sourcebrief"])
    sources = cast(list[dict[str, Any]], manifest["sources"])
    slug = str(identity["slug"])
    description = f"Use this SourceBrief remote repo agent for {identity['name']} questions."
    return (
        "---\n"
        f"name: {yaml_scalar(slug)}\n"
        f"description: {yaml_scalar(description)}\n"
        "---\n\n"
        f"# {identity['name']}\n\n"
        "This is a SourceBrief remote repo agent skill shim. Installing this raw `SKILL.md` only installs the Hermes skill; MCP configuration is a separate mandatory setup step.\n\n"
        "## Non-negotiable operating contract\n"
        "This repo agent is not ready unless all three pieces exist: this generated skill, the SourceBrief MCP server, and a CLI fallback path for setup/doctor/resource lifecycle. The skill decides *when* to use SourceBrief, MCP is the primary evidence path, and CLI is the fallback/toolbelt—not the main reasoning surface.\n\n"
        "## Runtime contract\n"
        "- Remote-only: do not assume the target repositories exist on this machine.\n"
        "- Do not run local `grep`, `rg`, `cat`, or filesystem edits for these repositories unless the user explicitly provides a separate local checkout for the current task.\n"
        "- Use `sourcebrief.get_agent_context` first, then `sourcebrief.grep_code`, `sourcebrief.read_file`, `sourcebrief.search_code`, or `sourcebrief.find_symbol` for exact follow-up inspection.\n"
        "- Cite repo-relative paths, resource IDs, and indexed commits/snapshots when SourceBrief returns them.\n"
        "- Treat indexed code as static evidence, not live production state.\n"
        "- Mutation policy is read-only by default. Patch generation and PR workflow are opt-in SourceBrief tools that require explicit project policy, scopes, and per-action approval; never claim remote write, test execution, deployment, or production mutation capability from this skill.\n\n"
        "## Required MCP setup\n"
        f"Configure the SourceBrief MCP endpoint separately: `{sourcebrief['mcp_endpoint']}`.\n"
        "Use a scoped bearer token through the `SOURCEBRIEF_TOKEN` environment variable or your runtime's secret manager. Do not place plaintext tokens in this skill.\n\n"
        "## Workflow\n"
        "1. Use this skill when the user asks about the listed project/repository scope.\n"
        "2. Call `sourcebrief.get_agent_context` with the user's question and an appropriate resource scope when known.\n"
        "3. Pick retrieval profiles intentionally: `hybrid` by default, `lexical` for exact identifiers/errors/config keys, `vector` for semantic discovery, `hybrid_rerank` when eval precision matters, and `graph` for architecture/impact/code-structure questions.\n"
        "4. If the answer needs exact evidence, use remote grep/read/search/symbol tools against indexed snapshots; do not fall back to local filesystem access.\n"
        "5. If MCP is unavailable, use CLI fallback only for diagnosis/setup: `sourcebrief doctor`, `sourcebrief runtime validate --run`, `sourcebrief skill install --dry-run`, or resource lifecycle commands. Do not answer from uncited memory.\n"
        "6. Preserve authorization and production-mutation boundaries.\n\n"
        "## Authorized sources in this generated pack\n"
        f"{source_lines(sources)}\n"
    )


def codex_agents(manifest: Mapping[str, Any]) -> str:
    identity = cast(Mapping[str, Any], manifest["identity"])
    sources = cast(list[dict[str, Any]], manifest["sources"])
    return (
        f"# {identity['name']} SourceBrief Remote Repo Agent\n\n"
        "You are using a SourceBrief remote repo agent. The checked-out Skill Pack is not the target source repository.\n\n"
        "Non-negotiable contract: load the generated instructions, use SourceBrief MCP as the primary evidence path, and keep `sourcebrief` CLI as setup/doctor/resource-lifecycle fallback only. If one of those pieces is missing, say the runtime is not fully installed before answering.\n\n"
        "- Remote-only: do not assume repository files exist in the current working directory.\n"
        "- Do not run local `grep`, `rg`, `cat`, or edits for target repositories unless the user explicitly provides a separate local checkout.\n"
        "- Use `sourcebrief.get_agent_context` first, then remote grep/read/search/symbol tools for exact follow-up inspection.\n"
        "- Retrieval profile guide: `hybrid` default, `lexical` exact identifiers/errors/config, `vector` semantic discovery, `hybrid_rerank` eval precision, `graph` architecture/impact.\n"
        "- Cite repo-relative paths, resource IDs, and indexed commits/snapshots from SourceBrief.\n"
        "- Treat indexed code as static evidence, not live production truth.\n"
        "- Read-only by default. Patch generation and PR workflow are opt-in only, require SourceBrief policy/scopes/per-action approval, and do not grant remote write/deploy/test execution by themselves.\n\n"
        "## Authorized sources\n"
        f"{source_lines(sources)}\n"
    )


def claude_md(manifest: Mapping[str, Any]) -> str:
    identity = cast(Mapping[str, Any], manifest["identity"])
    sources = cast(list[dict[str, Any]], manifest["sources"])
    return (
        f"# {identity['name']} SourceBrief Remote Repo Agent\n\n"
        "Use SourceBrief MCP for this repo agent. This instruction file is not a source checkout.\n\n"
        "Non-negotiable contract: this instruction file tells the agent when to use SourceBrief, MCP is the primary evidence path, and CLI is the setup/doctor/resource-lifecycle fallback. If skill + MCP + CLI fallback are not verified, say the runtime is not fully installed.\n\n"
        "- Remote-only: do not assume target repositories are local.\n"
        "- Do not use local `grep`, `rg`, `cat`, or filesystem edits for the target repos unless the user provides a separate checkout.\n"
        "- Call `sourcebrief.get_agent_context` first, then remote grep/read/search/symbol tools for exact follow-up inspection.\n"
        "- Retrieval profile guide: `hybrid` default, `lexical` exact identifiers/errors/config, `vector` semantic discovery, `hybrid_rerank` eval precision, `graph` architecture/impact.\n"
        "- Cite repo-relative paths, indexed commits/snapshots, and resource IDs.\n"
        "- Static indexed evidence is not live production state.\n"
        "- Ask for explicit approval before any mutation; patch generation and PR workflow are opt-in SourceBrief tools and do not grant remote write/deploy/test execution by themselves.\n\n"
        "## Authorized sources\n"
        f"{source_lines(sources)}\n"
    )


def mcp_json(manifest: Mapping[str, Any]) -> dict[str, Any]:
    identity = cast(Mapping[str, Any], manifest["identity"])
    sourcebrief = cast(Mapping[str, Any], manifest["sourcebrief"])
    server_name = f"sourcebrief-{identity['slug']}"
    server = {
        "url": sourcebrief["mcp_endpoint"],
        "headers": {"Authorization": "Bearer ${SOURCEBRIEF_TOKEN}"},
    }
    return {
        "hermes": {"mcp_servers": {server_name: server}},
        "claude": {"mcpServers": {server_name: server}},
        "codex": {"mcp_servers": {server_name: server}},
    }


def stable_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    stable = json.loads(json.dumps(manifest, sort_keys=True))
    freshness = stable.get("freshness")
    if isinstance(freshness, dict):
        freshness.pop("generated_at", None)
    return cast(dict[str, Any], stable)


def manifest_digest(manifest: Mapping[str, Any]) -> str:
    payload = json.dumps(stable_manifest(manifest), sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def readme(manifest: Mapping[str, Any], digest: str) -> str:
    identity = cast(Mapping[str, Any], manifest["identity"])
    sourcebrief = cast(Mapping[str, Any], manifest["sourcebrief"])
    slug = str(identity["slug"])
    return (
        f"# {identity['name']} Skill Pack\n\n"
        "This Skill Pack installs thin runtime adapters for a SourceBrief remote repo agent. "
        "It does not contain repository source, indexes, embeddings, eval history, or bearer tokens.\n\n"
        "## Files\n"
        "- `sourcebrief-agent.yaml` - canonical portable manifest.\n"
        "- `hermes/SKILL.md` - Hermes skill shim.\n"
        "- `codex/AGENTS.md` - Codex instruction adapter.\n"
        "- `claude/CLAUDE.md` - Claude Code instruction adapter.\n"
        "- `mcp.json` - MCP config snippets with token placeholders.\n\n"
        "## Hermes install\n"
        "Publish this pack to GitHub and install the pinned raw skill file, then configure MCP separately:\n\n"
        "```bash\n"
        f"hermes skills install https://raw.githubusercontent.com/<org>/<pack>/<tag-or-sha>/hermes/SKILL.md --name {slug}\n"
        "```\n\n"
        "## Codex\n"
        "Check out or copy this Skill Pack repository, then run Codex in a directory where `codex/AGENTS.md` is loaded. "
        "The checked-out pack is instruction/config material, not the target source repository.\n\n"
        "## Claude\n"
        "Use `claude/CLAUDE.md` as Claude Code instruction context for alpha support. Native Claude skill packaging is not claimed by this pack.\n\n"
        "## MCP and token setup\n"
        f"Configure MCP endpoint `{sourcebrief['mcp_endpoint']}` in your runtime. "
        "Set a scoped token through `SOURCEBRIEF_TOKEN` or your runtime secret manager. Do not commit plaintext tokens.\n\n"
        "## Pinning and drift\n"
        f"Manifest digest: `{digest}`. Pin GitHub installs to a tag or commit SHA for reproducibility. "
        "Mutable `main` installs are for development only. Regenerate the pack when the manifest digest changes.\n\n"
        "## Publishing boundary\n"
        "This zip is download-only. Future GitHub PR publishing must require explicit user approval, show the diff, "
        "and keep tokens as environment placeholders only. Patch generation and PR workflow remain opt-in and require explicit policy plus per-action approval records.\n"
    )


def changelog(manifest: Mapping[str, Any], digest: str) -> str:
    freshness = cast(Mapping[str, Any], manifest["freshness"])
    return (
        "# Changelog\n\n"
        "## Generated Skill Pack\n"
        f"- Generated at: `{freshness['generated_at']}`\n"
        f"- Manifest digest: `{digest}`\n"
        "- Phase 2 export package for GitHub-hosted, pinned runtime installation.\n"
    )


def golden_questions(manifest: Mapping[str, Any]) -> str:
    identity = cast(Mapping[str, Any], manifest["identity"])
    return (
        "# Placeholder golden evals for this remote repo agent.\n"
        "# Add project-specific questions after observing real usage.\n"
        f"agent: {json.dumps(str(identity['slug']))}\n"
        "questions: []\n"
    )


def zip_files(manifest: Mapping[str, Any]) -> dict[str, str]:
    digest = manifest_digest(manifest)
    return {
        "README.md": readme(manifest, digest),
        "sourcebrief-agent.yaml": manifest_yaml(manifest),
        "mcp.json": json.dumps(mcp_json(manifest), indent=2, sort_keys=True) + "\n",
        "hermes/SKILL.md": hermes_skill(manifest),
        "codex/AGENTS.md": codex_agents(manifest),
        "claude/CLAUDE.md": claude_md(manifest),
        "evals/golden-questions.yaml": golden_questions(manifest),
        "CHANGELOG.md": changelog(manifest, digest),
    }


def zip_bytes(manifest: Mapping[str, Any]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, content in zip_files(manifest).items():
            info = zipfile.ZipInfo(path, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    return buffer.getvalue()


def prepare_agent_pack(
    session: Session,
    workspace_id: UUID,
    project_id: UUID,
    principal: Principal,
    *,
    require_project_access: ProjectAccessGetter,
    current_project_resources: ProjectResourcesGetter,
) -> tuple[Project, dict[str, Any]]:
    require_scope(principal, "project:read")
    project = require_project_access(session, workspace_id, project_id, principal)
    profile = session.scalar(
        select(AgentProfile).where(
            AgentProfile.workspace_id == workspace_id,
            AgentProfile.project_id == project.id,
        )
    )
    agent_name = profile.name if profile is not None else project.name
    agent_description = profile.description if profile is not None else project.description
    resources = agent_pack_resources(current_project_resources(session, workspace_id, project_id), principal)
    metadata_by_snapshot = snapshot_metadata(session, resources)
    sources = [source_entry(resource, metadata_by_snapshot) for resource in resources]
    return project, manifest_dict(workspace_id, project, agent_name, agent_description, sources)
