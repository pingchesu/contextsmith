# Launch readiness 5-role review (#211)

Issue: [#211](https://github.com/pingchesu/sourcebrief/issues/211)
Parent: [#208](https://github.com/pingchesu/sourcebrief/issues/208)
Candidate SHA: `1107ef4` (`docs: capture self-improvement browser proof`)

## Evidence inputs reviewed

| Evidence | Current status |
| --- | --- |
| Claim ledger | [`docs/CLAIM_LEDGER.md`](../../CLAIM_LEDGER.md) keeps launch-facing claims separated into Current / RISK / Unsupported. |
| Proof manifest | [`docs/PROOF_ARTIFACTS.md`](../../PROOF_ARTIFACTS.md) links committed screenshots, runtime proof, proof-gap closures, Skill Export, real-corpus, and self-improvement browser proof. |
| Screenshot-backed 50Q | [`sourcebrief-launch-50q-20260630.md`](../sourcebrief-launch-50q-20260630.md) records current screenshot-backed 50Q walkthrough. |
| Proof gaps | [`proof-gaps-20260630/README.md`](../proof-gaps-20260630/README.md) closes Resource Map, Context Pack, and runtime doctor proof gaps. |
| Skill Export | [`skill-export-20260630/README.md`](../skill-export-20260630/README.md) closes approved/downloadable package proof. |
| Real-corpus regression | [`real-corpus-regression-20260630/README.md`](../real-corpus-regression-20260630/README.md) records current real-corpus evidence as **RISK**, not PASS. |
| Self-improvement browser proof | [`self-improvement-browser-20260630/README.md`](../self-improvement-browser-20260630/README.md) verifies the artifact-first no-silent-mutation UI surface. |

## Current open child risks

| Issue | Meaning | Launch impact |
| --- | --- | --- |
| [#229](https://github.com/pingchesu/sourcebrief/issues/229) | Temporal-memory gate remains RISK on current `hybrid` profile. | Blocks temporal-memory adoption/PASS wording; does not block local-alpha launch if temporal-memory claims remain RISK/excluded. |
| [#231](https://github.com/pingchesu/sourcebrief/issues/231) | Random-port browser proof stacks need matching CORS origin. | Setup/reproducibility risk; should be fixed before making random-port browser capture a fully automated gate. |
| [#233](https://github.com/pingchesu/sourcebrief/issues/233) | Launch-security probe can overstate security/failure-mode readiness. | Keeps security-boundary claims at RISK; blocks treating `make launch-security-probe` as a launch PASS gate. |
| [#234](https://github.com/pingchesu/sourcebrief/issues/234) | 50Q walkthrough runner/proof needs fail-fast cleanup, token cleanup, screenshot UUID hygiene, and stronger isolated-stack reproducibility. | Keeps screenshot-backed 50Q proof useful for local-alpha evidence but RISK for public/fully automated launch proof. |
| [#235](https://github.com/pingchesu/sourcebrief/issues/235) | Skill Export approved package proof embeds draft-status README wording. | Does not block acknowledging approved export metadata, but blocks treating the package README itself as unambiguous install guidance. |

## Local verification while preparing this review

```text
readiness evidence links/json blocks ok
23 passed in 0.29s
```

Focused tests:

```text
tests/unit/test_launch_50q_walkthrough.py
tests/unit/test_skill_export_contract.py
tests/unit/test_self_improvement_mvp_product.py
tests/unit/test_launch_security_probe.py
```

## Adopted async adversarial findings

Several earlier PR-review delegations completed after their PRs had already been merged. I re-validated the durable findings against current `main` before adopting them here.

| Source review | Current disposition |
| --- | --- |
| PR #223 runtime docs review | Adopted. `docs/AGENT_RUNTIME_USAGE.md` overstated `sourcebrief doctor` as a complete REST/MCP validator. This branch narrows `doctor` to a lightweight smoke test and points full validation to generated runtime validator commands. |
| PR #218/#224 launch-security probe reviews | Adopted. Current probe still has false-pass, redaction, browser-transcript, token-lifecycle, dev-auth, and cleanup risks. Opened [#233](https://github.com/pingchesu/sourcebrief/issues/233) and changed the claim ledger security-boundary row from `Current` to `RISK`. |
| PR #210/#225 50Q walkthrough reviews | Adopted. Current proof remains valuable but has runner cleanup/fail-fast, screenshot UUID hygiene, and reproducibility gaps. Opened [#234](https://github.com/pingchesu/sourcebrief/issues/234) and changed the claim ledger 50Q row from `Current` to `RISK`. |
| PR #226 Skill Export reviews | Adopted. Approved export metadata is present, but embedded package README says `Status: draft`; opened [#235](https://github.com/pingchesu/sourcebrief/issues/235). |
| PR #230 real-corpus review | Partly adopted. No readiness blocker beyond known `RISK` verdict and [#229](https://github.com/pingchesu/sourcebrief/issues/229); the public run plan also had a concrete local env-file path, which this branch replaces with a placeholder. |

## Role verdicts

The five required role lenses return a shared conclusion: the current evidence is useful for local-alpha review, but unresolved child risks block any blanket launch PASS.

| Role | Verdict | Adopted findings / disposition |
| --- | --- | --- |
| CEO / customer trust | RISK | Customer-facing trust is acceptable only for **local-alpha evidence review** wording. The claim ledger now prevents blanket PASS wording for real-corpus, 50Q public proof, and security-boundary gates while #229/#233/#234 remain open. |
| CTO / architecture, ops, security | BLOCK for launch PASS / RISK for local alpha | Architecture is demonstrable, but launch-security probe semantics are not trustworthy enough for a PASS gate (#233); random-port CORS setup (#231), temporal-memory quality (#229), and 50Q runner cleanup/reproducibility (#234) remain operational risks. |
| PO / onboarding and customer love | RISK | The product story is coherent for local alpha: screenshots, proof gaps, Skill Export, and self-improvement surface now have evidence. The story must avoid enterprise/public-SaaS, autonomous mutation, temporal-memory adoption, and security PASS claims until child issues close. |
| Tech Lead / reproducibility and implementation | RISK | Evidence is committed and link-checked, but several proof paths still rely on local/ignored run context or generated artifacts with caveats. This branch fixes the concrete `/tmp/...env` path and `doctor` validator overclaim, while #234/#235 track remaining reproducibility/package consistency work. |
| QA Lead / acceptance, flakiness, regression | BLOCK for launch PASS / RISK for local alpha | Focused tests pass locally, but QA cannot accept a launch PASS while probe gates can false-pass (#233), public screenshot hygiene is unresolved (#234), temporal-memory fails 18/50 (#229), and browser proof-stack CORS is not hardened (#231). |

## Draft synthesis boundary

This launch train can only be summarized as a **local-alpha evidence review with explicit RISK lanes**, not a blanket launch PASS, while #229/#231/#233/#234/#235 remain open. Safe wording must follow the claim ledger: local-alpha scope, self-improvement artifact surface, and runtime dry-run/apply boundaries can be described as current; real-corpus quality, screenshot-backed 50Q public/automated proof, and security-boundary launch gates remain RISK until their child issues are closed.
