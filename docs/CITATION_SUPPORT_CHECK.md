# Deterministic citation-support check

This document defines the MVP citation-support check for SourceBrief self-improvement issue [#167](https://github.com/pingchesu/sourcebrief/issues/167).

The first slice is intentionally deterministic. It does not try to solve full semantic claim extraction; it gives #161 reviewer runner and #164 validation gate a fail-closed citation lens over review bundles and golden fixtures.

## Implementation

```text
sourcebrief_shared.citation_support.citation_support_findings
sourcebrief_shared.citation_support.build_citation_support_report
```

The check consumes a `sourcebrief.review-bundle.v1` bundle and emits `sourcebrief.review-finding.v1` findings.

## MVP rules

For each `output.claim_ids[]` in a review bundle:

1. If no citation declares the claim ID in `citation.supports_claim_ids`, emit a `major` `unsupported_claim` finding.
2. If citations declare support but none of their snippet/title/path text contains any meaningful token from the claim ID, emit a `blocker` `citation_mismatch` finding.
3. Otherwise, the claim passes the deterministic MVP check.

This is a conservative fixture/gate check, not a replacement for later semantic review. Later work can add LLM or retrieval-backed claim extraction, but it should keep this deterministic control as a gate.

## Golden fixtures

The check is covered by the #172 fixtures:

| Bundle | Expected result |
| --- | --- |
| `docs/examples/self-improvement/review-bundle-docs-answer.json` | pass / no findings |
| `docs/examples/self-improvement/golden/review-bundle-unsupported-claim.json` | `major` `unsupported_claim` |
| `docs/examples/self-improvement/golden/review-bundle-citation-mismatch.json` | `blocker` `citation_mismatch` |

## Limitations

- It uses claim IDs and cited snippet/title/path tokens; it does not parse arbitrary answer prose into claims.
- A semantically wrong citation can still pass if the claim ID tokens appear in the snippet. The autonomous reviewer runner should add deeper checks later.
- A semantically correct citation can fail if claim IDs are poorly named. Producers should use descriptive claim IDs.

## Verification

```bash
uv run --extra dev python -m pytest tests/unit/test_citation_support.py -q
```
