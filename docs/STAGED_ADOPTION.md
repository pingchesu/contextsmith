# Staged adoption

This document describes the staged adoption workflow for SourceBrief self-improvement issue [#165](https://github.com/pingchesu/sourcebrief/issues/165).

A validation gate result is not a production change. Staged adoption creates a reviewable directory containing the accepted proposal, gate result, proposed patch, and receipt so a developer can decide what to apply in a normal PR/review flow.

## CLI usage

```bash
sourcebrief review stage \
  --proposal ./regression-proposals/quickstart-auth.json \
  --gate-result ./gate-results/quickstart-auth.json \
  --out-dir ./staged-adoption
```

The command writes a subdirectory named after the proposal ID, for example:

```text
staged-adoption/proposal-finding-learning-quickstart-gap/
  proposal.json
  gate-result.json
  proposal.patch
  README.md
  receipt.json
```

## Artifact contract

Receipt schema version:

```text
sourcebrief.staged-adoption-receipt.v1
```

The receipt records:

- source proposal, report, bundle, finding, and gate result IDs;
- target surface;
- staged proposal, gate result, patch, and summary files with `sha256:<64 hex>` digests;
- explicit apply command;
- explicit rollback command;
- discard command for removing the staged directory;
- `human_review_required=true`.

## Safety boundary

`sourcebrief review stage` **does not**:

- mutate prompts, skills, runtime packs, docs, tests, or code;
- push a branch or open/merge a PR;
- accept rejected gate results;
- stage proposals whose gate result does not match the proposal ID;
- stage proposals with `target_surface="unknown"`.

The generated `proposal.patch` is intentionally human-readable. Applying it is a separate explicit action, and the receipt includes a `git apply -R ...` rollback command.

## Verification

```bash
uv run --extra dev python -m pytest \
  tests/unit/test_staged_adoption.py \
  tests/unit/test_cli.py::test_cli_review_stage_writes_receipt_patch_and_does_not_login \
  tests/unit/test_cli.py::test_cli_review_stage_rejects_rejected_gate -q
```
