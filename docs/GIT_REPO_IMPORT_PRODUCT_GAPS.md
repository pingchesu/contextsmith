# Git Repo Import Product Gaps

This document records product gaps observed while reviewing the current Git repository import path. It is a backlog for turning Git import from a functional connector into a mature, enterprise-grade source onboarding experience.

## Current expected flow

Today, Git repo import is expected to work as:

```text
Git repo URL
→ Resource(type=git)
→ refresh/index run
→ source snapshot pinned by commit SHA
→ chunks / lexical index / embeddings / code symbols / graph
→ search, code search, agent-context, MCP context
→ Resource Map
→ Context Pack
→ generated Skill Export / Repo Agent view
```

The current implementation already treats repo code as source material only. The worker should clone/read bounded text/source files, capture commit metadata, and avoid executing repo code.

## Product gaps to close

### G1. Private repository authentication is not productized

**Problem**

The visible flow is mostly shaped around public HTTPS repos and local smoke-test repositories. Private repositories need a first-class credential/connection model rather than ad hoc token entry.

**User impact**

Enterprise users will expect to connect GitHub/GitLab/Bitbucket repos with a normal account/app flow. They should not paste raw bearer tokens into arbitrary forms or docs.

**Target behavior**

- Named Git connections live in Settings or an account/integration area.
- Resource creation selects an existing connection by human label.
- Tokens/secrets are stored server-side, encrypted/secret-managed, and never shown again.
- The import form explains permission scope before connecting.
- Failed auth returns actionable messages without leaking secrets.

**Acceptance**

- Add private repo using a named connection.
- Refresh succeeds without pasting credentials into the source form.
- Revoking the connection blocks future refreshes with a clear error.
- Audit event records who created/used the connection without storing plaintext secrets.

### G2. Import progress is not stage-oriented enough

**Problem**

Users need to see where import is spending time: clone/fetch, checkout, file filtering, chunking, embeddings, symbol extraction, graph build, artifact compilation.

**User impact**

A repo import can take long enough that a simple queued/running status feels stuck or unreliable.

**Target behavior**

- Index run progress has named stages.
- Each stage records started/finished timestamps and counts where possible.
- The Sources page displays the active stage and last completed stage.
- Failures point to the failed stage.

**Acceptance**

- During a real repo import, UI shows at least clone/fetch, scan/filter, index, and post-processing stages.
- A forced failure in a stage surfaces that exact stage in API/UI.
- Operators can inspect stage history from the resource detail view.

### G3. Skipped-file reporting is insufficient as product evidence

**Problem**

The connector skips generated/dependency/binary/oversized content, but users need a reviewable report of what was skipped and why.

**User impact**

Without skipped-file evidence, users cannot tell whether SourceBrief ignored important files or correctly filtered noise.

**Target behavior**

- Snapshot metadata records skipped-file counts by reason.
- Source detail shows top skipped paths and reason categories.
- Large reports are paginated/downloadable.
- Skips are included in Resource Map coverage warnings when they affect source trust.

**Acceptance**

- Import a repo with binary, oversized, dependency, and ignored files.
- UI/API reports counts by skip reason.
- At least the first N skipped paths are inspectable with reason and size.

### G4. First successful query is not guided enough

**Problem**

After indexing succeeds, the product should immediately guide the user to ask a source-scoped question and inspect citations.

**User impact**

Users may not understand what to do after import or how to verify that the repo is actually useful.

**Target behavior**

- Successful import shows a clear next action: “Ask this source”.
- Suggested prompts are generated from repo metadata/file coverage, not generic filler.
- The first answer emphasizes citations, paths, and commit metadata.

**Acceptance**

- After Git import succeeds, source detail exposes a primary source-scoped query action.
- The returned answer includes citations tied to the imported commit.
- Empty/low-confidence results explain what coverage may be missing.

### G5. Freshness and diff UX for repo updates is immature

**Problem**

Scheduled/manual refresh should explain what changed between snapshots, not just that reindexing succeeded.

**User impact**

Users need to decide whether a refreshed repo changes the generated context, Context Pack, Skill Export, or Repo Agent behavior.

**Target behavior**

- Snapshot comparison shows added/changed/deleted files.
- Diff view indicates affected chunks, symbols, graph nodes/edges, Resource Maps, Context Packs, Skill Exports, and Repo Agent drafts.
- Repo updates create draft changes; they do not silently republish runtime artifacts.

**Acceptance**

- Refresh a repo from commit A to commit B.
- UI shows file-level and artifact-level impact.
- Existing published pack/export remains pinned until a reviewer publishes a new version.

### G6. Repo Agent / Skill / Context Pack terminology needs stronger product guardrails

**Problem**

The current pipeline has several adjacent concepts: Resource, Resource Map, Context Pack, Skill Export, Repo Agent. The UI must not collapse them into one vague “skill” concept.

**User impact**

If users think “import repo” immediately creates an agent/skill, they will misunderstand review, freshness, and runtime boundaries.

**Target behavior**

- Importing a repo creates a Source/Resource.
- Resource Map is the reviewable deterministic source summary.
- Context Pack is the curated, published, pinned evidence bundle.
- Skill Export is a thin runtime adapter generated from a published Context Pack.
- Repo Agent is a managed agent profile/view over resources, packs, exports, and update policy.

**Acceptance**

- UI labels and empty states teach the distinction.
- Generated skill pages state that the package contains instructions only, not source corpus.
- Repo Agent pages show which pack/export/version they are bound to.

### G7. Git Resource Map review path is not first-class in the Sources UI

**Problem**

The backend can compile Resource Map artifacts for Git resources, but the current Sources detail UI exposes the Resource Map review controls primarily for folder bundles. That means the documented pipeline is true architecturally, but Git users do not get an obvious in-product path from imported repo to Resource Map review.

**User impact**

Users can import and query a repo, but may not discover or complete the reviewable artifact step that should lead into Context Packs, Skill Exports, and Repo Agent versions.

**Target behavior**

- Git source detail exposes Resource Map compile/recompile, validation, approval/rejection, citations, and coverage rows.
- Git Resource Map UI includes commit/snapshot/path/line provenance.
- Folder bundle-specific manifest and diff UX stays separate from generic Resource Map UX.
- Context Pack creation can select approved Git Resource Map artifacts without forcing users through hidden IDs or API calls.

**Acceptance**

- Import a Git repo, index it, and compile a Resource Map from the Sources page.
- Approve the Git Resource Map and create a Context Pack draft from it using human labels.
- Generated Skill Export can be created from the published pack without any UUID copy/paste.

### G8. Graph merge needs enterprise hardening for cross-repo repo-import workflows

**Problem**

Graph Merge already has API/UI surface, candidate review, input inspection, and path query. The remaining Git-import gap is product hardening: making cross-repo graph merge explainable, safe, and easy to reason about for imported repos.

**User impact**

Cross-repo architecture or ownership answers can become misleading if graph equivalence, provenance, freshness, and authorization state are not visible beside merged graph results.

**Target behavior**

- Merged graph views show source resource, snapshot, path, and line provenance wherever available.
- Ambiguous equivalence candidates are reviewable with clear impact on downstream queries.
- Graph merge outputs show freshness/invalidated-pack warnings when source repos change.
- Runtime MCP graph queries surface merge provenance rather than only merged node IDs.

**Acceptance**

- Merge two repo graph versions and query a path between deterministically seedable nodes.
- UI shows which input graph/resource/snapshot contributed each node/edge.
- Unauthorized resources do not leak through merged graph output.

### G9. Enterprise import controls are incomplete

**Problem**

Large repos need predictable limits, cost controls, retry behavior, and operator visibility.

**User impact**

Without controls, repo import can become expensive, slow, or hard to support.

**Target behavior**

- Per-resource and per-workspace import limits are visible before import.
- Admins can set max files, max bytes, clone timeout, and provider/indexing budget.
- Index runs have retry/cancel controls.
- Operations page surfaces stuck imports and queue latency.

**Acceptance**

- Operator can cancel a long-running import.
- Retry preserves prior failure evidence.
- Exceeding a limit produces a clear, non-500 error and records the reason.

## Suggested PR slicing

1. **Repo import evidence UX** — stage progress + skipped-file report + first query CTA.
2. **Private Git connections** — named connection model and secret handling.
3. **Repo refresh diff** — snapshot diff and artifact impact report.
4. **Terminology hardening** — UI copy and docs for Resource / Resource Map / Context Pack / Skill Export / Repo Agent.
5. **Git Resource Map UI path** — compile/approve Git Resource Maps and feed them into Context Packs without UUIDs.
6. **Cross-repo graph merge hardening** — provenance, freshness warnings, and runtime graph-query safety.
7. **Operational controls** — retry/cancel/limits/stuck-run visibility.

## Non-goals for the immediate next PR

- Running user repository code.
- Auto-publishing refreshed Context Packs or Skill Exports.
- Treating generated Skill Export as embedded source corpus.
- Building one MCP server per imported repo.
