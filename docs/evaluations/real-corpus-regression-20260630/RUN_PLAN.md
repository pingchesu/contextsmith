# SourceBrief real-corpus regression run plan (#214)

Run date: 2026-06-30
Issue: [#214](https://github.com/pingchesu/sourcebrief/issues/214)
Parent: [#208](https://github.com/pingchesu/sourcebrief/issues/208)
Candidate commit: `5e6ae69526d3db8b1f19103171062bd2b8480e81`
Branch used for documentation/artifacts: `proof/real-corpus-regression-214`

## Predeclared corpus and manifests

### General real-corpus gate

Question bank: `examples/awesome-agent-harness-50q/questions.json`

- Questions: 50
- Source matrix:
  - Superpowers — <https://github.com/obra/superpowers>
  - ECC — <https://github.com/affaan-m/ECC>
  - Matt Pocock Skills — <https://github.com/mattpocock/skills>
  - gstack — <https://github.com/garrytan/gstack>
  - DeerFlow — <https://github.com/bytedance/deer-flow>
- Runner: `scripts/run_awesome_agent_harness_eval.py`
- Route coverage: `/retrieval-evals`, `/agent-context`, resource-ref selection proof
- Import policy: preserve first wide failures, then bounded retry if needed; every bounded/partial source must remain marked partial/limited in the final verdict.

### Temporal-memory gate

Manifest: `demo/evo_temporal_50q/eval_manifest.json`

- Questions: 50
- Manifest digest: `sha256:840e2e0897b864f4786e9f336a77a76183a4d457fe86b4bd8c247bd25852e32c`
- Ordered fixture: `demo/evo_temporal_50q/temporal_fixture.md`
- Current #214 scope: refresh/validate the gate design and run only when the manifest is bound to real resource/snapshot IDs. If runtime binding is not implemented in this slice, report it as RISK/BLOCK instead of faking a temporal pass.

## Provider/profile mode

Current local stack provider health:

- Embedding: `hashing` / `sourcebrief-hashing-v1`, `dev_quality=true`
- Rerank: `term-overlap` / `sourcebrief-term-overlap-v1`, `dev_quality=true`

These providers are acceptable for regression evidence but not launch-ready quality claims. Any result under this provider mode must be labelled RISK unless a separate production-quality provider run is added.

## Predeclared thresholds

| Lane | PASS threshold | RISK / BLOCK rule |
| --- | --- | --- |
| Mechanical/API execution | 50/50 requests accounted for, schema-valid raw outputs preserved, no missing question rows | Any missing row, unhandled exception, or unpreserved failure is BLOCK |
| Wrong-resource safety | wrong-repo / wrong-resource citations = 0 | Any wrong-resource citation is BLOCK |
| Unsupported claims | unsupported final-answer claims = 0 | Any unsupported claim is BLOCK |
| Retrieval/context quality | all questions have relevant citations and top paths are plausible for the allowed corpus | Low-signal top paths, citation duplication hiding poor evidence, or missing expected corpus warnings is RISK/BLOCK depending severity |
| Human answer/demo quality | synthesized end-user answers are supported by citations | Answer-ready context without synthesized final answers is PARTIAL/RISK, not PASS |
| Import health | every source has queryable evidence or explicit partial/failure accounting | Hidden partial corpus, failed/no-snapshot resources presented as queryable, or missing retry guidance is BLOCK |
| Provider quality | production-quality provider health | dev-quality hashing/term-overlap forces final launch verdict to RISK even when mechanical gates pass |

## Commands to run

```bash
# Load the ignored local proof-stack environment for the active run.
# The file contains browser-visible API/web URLs, random ports, and local credentials;
# do not commit the concrete env-file path or its values.
source <local-proof-stack-env>
OUT="artifacts/e2e/214-$(date -u +%Y%m%d%H%M%S)-awesome-agent-harness"
SOURCEBRIEF_API_URL="$SOURCEBRIEF_API_URL" SOURCEBRIEF_WEB_URL="$SOURCEBRIEF_WEB_URL" \
  python scripts/run_awesome_agent_harness_eval.py \
  --api-url "$SOURCEBRIEF_API_URL" \
  --web-url "$SOURCEBRIEF_WEB_URL" \
  --output-dir "$OUT" \
  --slug "issue214-$(date -u +%Y%m%d%H%M%S)" \
  --index-timeout 900 \
  --sourcebrief-commit "5e6ae69526d3db8b1f19103171062bd2b8480e81" \
  --allow-dev-quality-providers
```

## Non-goals

- Do not use current dev-quality provider results as customer-facing launch PASS.
- Do not shrink the Awesome Agent Harness 50Q bank unless the omitted claim is explicitly excluded from launch scope.
- Do not fabricate temporal-memory runtime evidence if the placeholder manifest has not been bound to real resource/snapshot IDs.
