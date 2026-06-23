# Deep docs proof and IA cleanup

## Implementation status

Implemented in this PR:

- Rewrote `CONCEPTS.md` around the product mental model: `Source -> Snapshot -> Evidence -> Review -> Runtime`.
- Added `docs/PROOF_ARTIFACTS.md` as the single proof manifest for screenshots, captured outputs, real-service tests, and proof gaps.
- Reorganized `docs/README.md` into primary path, proof/demos, runtime/operations, reference, deep specs, follow-up trackers, and archive.
- Updated `AGENT_RUNTIME_USAGE.md` for the current MCP golden path: `sourcebrief.ask`, `sourcebrief.discover`, and `sourcebrief.lookup`, plus per-runtime setup/reload/failure-mode guidance.
- Updated README, Quick start, Demo, and Status links so proof artifacts are visible without turning the front door into a text wall.

## Remaining follow-ups

These are intentionally not faked here:

- Capture a real Resource Map rendered/API output artifact.
- Capture a real Context Pack `get_context_pack` + pack-scoped `ask` output artifact.
- Capture a real approved Skill Export manifest/validation report artifact.
- Capture a clean terminal transcript for `sourcebrief doctor --query` and `runtime setup hermes --dry-run`.

## Problem

The front door now explains SourceBrief better, but deep docs still mixed product concepts, runtime guidance, specs, milestones, and internal history. The docs needed a second pass that made runtime usage and proof artifacts complete without turning the README back into a wall of text.

## Scope

- Rewrite `CONCEPTS.md` around the product mental model from README.
- Split or restructure runtime guidance into clear paths:
  - Hermes
  - Claude Code
  - Codex
  - Cursor/custom MCP.
- Add proof artifacts for Resource Map, Context Pack, Skill Pack export, graph/query output, and runtime validation where available.
- Clean the docs index so specs/milestones/archive are discoverable but not primary onboarding paths.
- Add status labels for alpha/experimental/archive docs.

## Non-goals

- No new product capabilities unless required to produce proof artifacts.
- No deletion of historical specs without separate review.
- No fake screenshots or mock-only output.

## Acceptance criteria

- A new reader can move from README -> concepts -> runtime guide without hitting milestone/spec walls.
- Runtime-specific docs include exact config shape, auth boundary, reload/validation step, and failure modes.
- Proof artifacts are either captured from real local runs or explicitly marked as unavailable/follow-up.
- Archive/spec docs are demoted with clear labels.
- Docs links and examples pass sanity checks.

## Verification

- Markdown link/fence checks.
- Secret/raw ID scan for new proof artifacts.
- At least two docs review passes: reader/product and technical/security.
- Real local stack evidence for any new proof claim.
