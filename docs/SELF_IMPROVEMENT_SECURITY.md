# Self-improvement artifact security baseline

This document is the security and privacy baseline for SourceBrief self-improvement artifacts. It is the first implementation slice for [#169](https://github.com/pingchesu/sourcebrief/issues/169) and must be in place before durable review bundle capture in [#160](https://github.com/pingchesu/sourcebrief/issues/160).

Self-improvement artifacts are governed product artifacts, not arbitrary transcript dumps.

## Artifact classes

| Sensitivity | Meaning | Default reviewer egress |
| --- | --- | --- |
| `public` | Public docs, OSS examples, sanitized demo output. | Local/mock or approved internal/external backend. |
| `internal` | Product/runtime metadata that is not public but should not contain raw secrets. | Local/mock and approved internal backend. |
| `private` | Customer, tenant, repository, or workspace-specific evidence. | Local/mock only unless workspace/project policy explicitly opts in to an external reviewer. |
| `secret` | Known secret-bearing payloads, raw credentials, or artifacts that failed redaction. | No external egress; local quarantine or purge path only. |

## Required metadata

Every review bundle, reviewer finding, proposal, gate result, staged patch, and observability summary should carry or inherit:

- `sensitivity`
- `retention_days`
- `allowed_reviewer_backends`
- `reviewer_backend`
- `egress_decision`
- `external_reviewer_opt_in`
- `purge_derived_artifacts`
- `completeness`: `complete`, `redacted_partial`, or `insufficient_evidence`
- `redaction_counts`
- `scope.workspace_id`
- `scope.project_id`
- `scope.resource_ids`
- `scope.context_pack_key`

The code baseline lives in `sourcebrief_shared.self_improvement_security` so later schema work can reuse it instead of redefining safety fields.

## Redaction contract

Before a bundle is stored or sent to any reviewer backend, SourceBrief must redact:

- bearer tokens and SourceBrief `cs_*` tokens;
- GitHub, Slack, OpenAI, AWS-looking tokens;
- generic `token=`, `api_key=`, `secret=`, `password=`, and `session_token=` assignments;
- dictionary values under secret-looking keys such as `Authorization`, `cookie`, `password`, `secret`, `token`, and `api_key`;
- local private paths under `/home/<user>/...`, `/Users/<user>/...`, and equivalent `file://` forms.

Redaction must be deterministic and testable. If redaction removes evidence needed for review, the bundle should be marked `redacted_partial`; if the bundle lacks enough evidence to validate the answer, it should be marked `insufficient_evidence` rather than guessed over.

## Permission and scope contract

A self-improvement reviewer inherits the originating task scope:

- same workspace;
- same project;
- same resource subset if the originating token/task was resource-scoped;
- same context pack if the review is about a generated agent/runtime artifact.

A reviewer must never widen from a resource-scoped answer to project-wide evidence or from one workspace/project to another. The baseline helper `ReviewArtifactScope.require_allows(...)` exists so bundle capture and reviewer execution can fail closed when later implementation issues wire this into API/CLI flows.

## Reviewer egress policy

Reviewer execution is a separate trust decision from bundle storage.

- `local`, `mock`, and `offline` reviewers are treated as local-only.
- A backend not listed in `allowed_reviewer_backends` is denied.
- `private` artifacts cannot use non-local reviewer backends unless the workspace/project explicitly opts in.
- `secret` artifacts cannot opt in to external reviewer egress.
- Every reviewer run must record backend identity and the resulting egress decision.

## Retention and purge

The purge target for a bundle must include derived artifacts:

1. review bundle;
2. reviewer report/finding;
3. regression or learning proposal;
4. validation gate result;
5. staged patch/receipt;
6. observability/history summaries.

Until a durable DB/storage implementation exists, issue #169 defines the metadata and helper contract that later bundle schema/storage issues must use. Issues #159 and #160 must not create durable bundle storage that omits these fields.

## Verification

Current tests:

```bash
uv run --extra dev python -m pytest tests/unit/test_self_improvement_security.py -q
```

The test suite covers token/password/path redaction, secret-key redaction, resource-scope preservation, reviewer egress denial, secret-artifact external egress rejection, and required security metadata generation.
