from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sourcebrief_shared.self_improvement_security import (
    BundleCompleteness,
    RedactionReport,
    ReviewArtifactPolicy,
    ReviewArtifactScope,
    build_security_metadata,
    redact_review_artifact,
)

REVIEW_BUNDLE_SCHEMA_VERSION = "sourcebrief.review-bundle.v1"

BundleKind = Literal["answer", "cli_demo", "pr_review", "runtime_agent_context"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReviewBundleScope(StrictModel):
    workspace_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    resource_ids: list[str] = Field(default_factory=list)
    context_pack_key: str | None = None


class ReviewBundleSecurity(StrictModel):
    sensitivity: Literal["public", "internal", "private", "secret"]
    retention_days: int = Field(ge=0)
    allowed_reviewer_backends: list[str] = Field(min_length=1)
    reviewer_backend: str = Field(min_length=1)
    egress_decision: Literal["local_only", "approved_internal", "approved_external", "denied"]
    external_reviewer_opt_in: bool = False
    purge_derived_artifacts: bool = True
    completeness: Literal["complete", "redacted_partial", "insufficient_evidence"]
    redaction_counts: dict[str, int] = Field(default_factory=dict)
    scope: ReviewBundleScope


class SourceRef(StrictModel):
    resource_id: str = Field(min_length=1)
    source_snapshot_id: str | None = None
    commit_sha: str | None = None
    path: str | None = None
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    content_hash: str | None = None
    title: str | None = None

    @field_validator("line_end")
    @classmethod
    def line_end_after_start(cls, value: int | None, info: Any) -> int | None:
        start = info.data.get("line_start")
        if value is not None and start is not None and value < start:
            raise ValueError("line_end must be >= line_start")
        return value


class CitationRef(StrictModel):
    citation_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    source_ref: SourceRef
    snippet: str | None = None
    snippet_hash: str | None = None
    supports_claim_ids: list[str] = Field(default_factory=list)


class ToolProof(StrictModel):
    proof_id: str = Field(min_length=1)
    kind: Literal["cli", "api", "mcp", "test", "browser", "git", "other"]
    command: list[str] = Field(default_factory=list)
    status: Literal["passed", "failed", "skipped", "not_run"]
    exit_code: int | None = None
    stdout_excerpt: str | None = None
    stderr_excerpt: str | None = None
    artifact_uri: str | None = None


class VerificationLog(StrictModel):
    command: str = Field(min_length=1)
    status: Literal["passed", "failed", "skipped", "not_run"]
    output_excerpt: str | None = None
    artifact_uri: str | None = None


class RuntimeContext(StrictModel):
    sourcebrief_commit: str | None = None
    runtime: str | None = None
    model_backend: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None
    skill_or_agent_pack_version: str | None = None
    retrieval_profile: str | None = None
    top_k: int | None = Field(default=None, ge=1)
    rerank_enabled: bool | None = None
    max_chars: int | None = Field(default=None, ge=1)


class ReviewBundleInput(StrictModel):
    original_query: str = Field(min_length=1)
    task_brief: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    user_corrections: list[str] = Field(default_factory=list)


class ReviewBundleOutput(StrictModel):
    summary: str = Field(min_length=1)
    body: str = Field(min_length=1)
    claim_ids: list[str] = Field(default_factory=list)


class ReviewBundle(StrictModel):
    schema_version: Literal["sourcebrief.review-bundle.v1"]
    bundle_id: str = Field(min_length=1)
    kind: BundleKind
    created_at: datetime
    input: ReviewBundleInput
    output: ReviewBundleOutput
    scope: ReviewBundleScope
    security: ReviewBundleSecurity
    runtime: RuntimeContext = Field(default_factory=RuntimeContext)
    source_refs: list[SourceRef] = Field(default_factory=list)
    citations: list[CitationRef] = Field(default_factory=list)
    tool_proof: list[ToolProof] = Field(default_factory=list)
    verification_logs: list[VerificationLog] = Field(default_factory=list)
    reviewer_notes: list[str] = Field(default_factory=list)

    @field_validator("security")
    @classmethod
    def security_scope_matches_bundle_scope(
        cls,
        security: ReviewBundleSecurity,
        info: Any,
    ) -> ReviewBundleSecurity:
        scope = info.data.get("scope")
        if scope is not None and security.scope != scope:
            raise ValueError("security.scope must match bundle scope")
        return security


def sanitize_review_bundle_payload(
    payload: dict[str, Any],
    *,
    policy: ReviewArtifactPolicy,
    scope: ReviewArtifactScope,
    reviewer_backend: str,
    completeness: BundleCompleteness,
) -> tuple[dict[str, Any], RedactionReport]:
    redacted_payload, report = redact_review_artifact(payload)
    if not isinstance(redacted_payload, dict):
        raise TypeError("review bundle payload must be an object")
    redacted_payload["security"] = build_security_metadata(
        policy=policy,
        scope=scope,
        reviewer_backend=reviewer_backend,
        completeness=completeness,
        redaction_report=report,
    )
    return redacted_payload, report


def load_review_bundle(path: str | Path) -> ReviewBundle:
    return ReviewBundle.model_validate_json(Path(path).read_text(encoding="utf-8"))


def review_bundle_json_schema() -> dict[str, Any]:
    return ReviewBundle.model_json_schema()


def write_review_bundle_json_schema(path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(review_bundle_json_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
