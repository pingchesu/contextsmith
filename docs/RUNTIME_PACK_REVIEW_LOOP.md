# Runtime-pack review-loop contract

This document describes the runtime-pack and generated-skill integration for SourceBrief self-improvement issue [#173](https://github.com/pingchesu/sourcebrief/issues/173).

## Shipped boundary

Generated SourceBrief skill/agent-pack text now carries an explicit self-improvement review-loop boundary:

```text
review bundle -> reviewer report -> proposal -> validation gate -> staged receipt -> history
```

The boundary is instructional, not mutating. A reviewer finding may produce a proposal targeting `runtime_pack`, but SourceBrief does not patch a user's installed runtime config or skill directory from that proposal.

## What runtime-pack proposals mean

`unsafe_mutation` findings map to `target_surface="runtime_pack"`. The generated proposal requires:

- preserving the SourceBrief review/citation/safety contract in generated skill or agent-pack output;
- staging wording changes through validation gate and staged adoption;
- avoiding silent installed-runtime config changes.

## Generated skill contract

`SKILL.md` includes a `Self-improvement review loop boundary` section that tells the agent to:

1. capture/load a `sourcebrief.review-bundle.v1` artifact;
2. run `sourcebrief review run`;
3. use `sourcebrief review propose` and `sourcebrief review gate`;
4. use `sourcebrief review stage` for a human-reviewable patch/receipt;
5. inspect `sourcebrief review history list/show` before changing product docs, generated skills, runtime packs, prompts, or code.

The existing three-piece runtime contract remains required:

- generated skill/agent pack;
- MCP-first cited evidence path;
- CLI fallback/control plane for setup, validation, install/uninstall, resource lifecycle, and automation.

## Non-goals

- Do not directly patch a user's installed Hermes/Claude/Codex/Cursor runtime config.
- Do not install generated skill changes from a reviewer opinion without a separate guarded install/apply step.
- Do not claim native runtime integration beyond the shipped skill export and CLI artifact path.

## Verification

- Generated skill validation fails if the self-improvement boundary disappears from `SKILL.md`.
- Proposal tests assert `unsafe_mutation` findings produce `runtime_pack` proposals with staged-adoption language.
- Integration tests assert generated `SKILL.md` contains the review-loop commands and installed-runtime non-mutation boundary.
