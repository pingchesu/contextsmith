# Review bundle schema

Review bundles are the stable artifacts used by SourceBrief self-improvement. They replace raw day-long transcript review with bounded, replayable evidence.

This document closes the design slice for [#159](https://github.com/pingchesu/sourcebrief/issues/159). It builds on the security baseline in [Self-improvement artifact security](SELF_IMPROVEMENT_SECURITY.md), which must remain a dependency for bundle capture and reviewer execution.

## Schema version

Current typed schema:

```text
sourcebrief.review-bundle.v1
```

Python model:

```text
sourcebrief_shared.review_bundle.ReviewBundle
```

The model is strict: unexpected fields are rejected so producers do not quietly persist unreviewed payload shapes.

## Required top-level fields

| Field | Required | Purpose |
| --- | --- | --- |
| `schema_version` | yes | Must be `sourcebrief.review-bundle.v1`. |
| `bundle_id` | yes | Stable artifact identifier. |
| `kind` | yes | `answer`, `cli_demo`, `pr_review`, or `runtime_agent_context`. |
| `created_at` | yes | Timestamp for retention and replay. |
| `input` | yes | Original query/task prompt, brief, acceptance criteria, non-goals, and user corrections. |
| `output` | yes | Final answer/PR/demo summary, body, and optional claim IDs. |
| `scope` | yes | Workspace/project/resource/context-pack boundary inherited from the originating task. |
| `security` | yes | Sensitivity, retention, reviewer backend/egress decision, redaction counts, completeness, purge policy, and mirrored scope. |
| `runtime` | optional object | SourceBrief commit, runtime, model/backend, prompt or skill-pack version, retrieval profile, top-k/rerank/max_chars. |
| `source_refs` | optional list | Snapshot/commit/path/line/content-hash evidence references. |
| `citations` | optional list | Human label plus machine-readable source refs and supported claim IDs. |
| `tool_proof` | optional list | CLI/API/MCP/test/browser/git proof excerpts and artifacts. |
| `verification_logs` | optional list | Verification command status and output excerpts. |
| `reviewer_notes` | optional list | Human-safe notes about capture or review. |

## Security requirements

Every bundle must include `security` metadata from `sourcebrief_shared.self_improvement_security`:

- `sensitivity`
- `retention_days`
- `allowed_reviewer_backends`
- `reviewer_backend`
- `egress_decision`
- `external_reviewer_opt_in`
- `purge_derived_artifacts`
- `completeness`
- `redaction_counts`
- `scope`

`security.scope` must match the top-level bundle `scope`. This prevents a producer from storing a resource-scoped bundle while reporting a looser project-wide security boundary.

The public-safe examples live under `docs/examples/self-improvement/`:

- [review-bundle-docs-answer.json](examples/self-improvement/review-bundle-docs-answer.json)
- [review-bundle-pr-review.json](examples/self-improvement/review-bundle-pr-review.json)

## Redaction and completeness

Before durable storage or reviewer egress, producers should call `sanitize_review_bundle_payload(...)` or an equivalent flow that uses the same #169 redaction helpers.

Completeness values:

| Value | Meaning |
| --- | --- |
| `complete` | Bundle has enough cited evidence and proof for reviewer validation. |
| `redacted_partial` | Some evidence was removed for safety, but remaining evidence may still support review. |
| `insufficient_evidence` | Bundle should not be used for claims/gates; it needs more source proof. |

A reviewer should not invent missing proof for `redacted_partial` or `insufficient_evidence` bundles.

## Forward compatibility

Version changes should be explicit:

- Additive optional fields may remain in `sourcebrief.review-bundle.v1` only if tests and docs are updated.
- Removing/renaming fields or changing meanings requires a new schema version.
- Consumers should fail closed on unknown top-level fields for v1.

## Verification

Focused verification:

```bash
uv run --extra dev python -m pytest tests/unit/test_review_bundle.py -q
```

The tests validate typed models, bundled examples, public-safe redaction, security scope matching, and generated JSON schema shape.
