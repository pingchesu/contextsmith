# Concepts

SourceBrief has a few terms that sound similar. This page defines them in user-facing language.

## The short version

```text
Source -> Snapshot -> Resource Map -> Context Pack -> Runtime context / Skill Pack
```

A source is something you connect. A snapshot is the exact version SourceBrief indexed. A Resource Map explains what SourceBrief found. A Context Pack is a reviewed, pinned bundle of evidence. Runtime context and Skill Packs are how agents use that evidence.

## Terms

| Term | Plain meaning | When you care |
| --- | --- | --- |
| Workspace | A tenant boundary for users, projects, tokens, and audit events. | When administering teams or access. |
| Project | A scoped context space, usually for a product, service, or repo group. | When choosing what an agent can query. |
| Source / Resource | A connected repo, doc, URL, runbook, upload, or zip folder bundle. | When adding knowledge to SourceBrief. |
| Snapshot | The exact indexed version of a source. For Git this includes commit information. | When auditing where an answer came from. |
| Chunk | A searchable piece of indexed text with citation metadata. | Mostly for retrieval/debugging. |
| Code symbol | A deterministic symbol extracted from source files when applicable. | When agents need code-aware context. |
| Resource graph | Relationships between resources, directories, files, and code symbols. | When following source structure, dependencies, or change impact. |
| Resource Map | A reviewable, citation-backed map of a repo or folder. | When onboarding an agent or understanding a codebase. |
| Context Packet | A cited retrieval result for a question. | When an API client needs ranked snippets and citations. |
| Agent Context | A runtime-shaped response for Hermes, Claude, Codex, Cursor, or API clients. | When serving context to an agent session. |
| Context Pack | A versioned, published evidence bundle built from approved artifacts. | When you want stable context for repeatable agent work. |
| Skill Export / Skill Pack | An installable/runtime package generated from a published Context Pack. | When you want reusable, citation-backed agent instructions and references. |
| Repo Agent | A managed profile/view over Git resources, Context Packs, and exports. | When treating a repo as an agent-ready source, not as an autonomous actor. |
| MCP tools | JSON-RPC tools that let agent runtimes query SourceBrief. | When integrating Claude, Codex, Cursor, Hermes, or custom agents. |

## What SourceBrief returns

SourceBrief does not try to be the final author of truth. It returns evidence that an agent or human can inspect:

- source name
- path or title
- line range or ordinal
- snapshot id
- commit SHA when available
- content hash
- retrieval score and graph/code-symbol hints
- runtime instructions for the caller

## Resource Map vs Context Pack

A Resource Map answers:

> What did SourceBrief find in this source, and where should an agent start?

A Context Pack answers:

> Which approved evidence bundle should an agent use for this task or project?

Resource Maps are source-specific. Context Packs can combine approved artifacts and coverage across sources.

## Skill Pack vs repo agent

A Skill Pack is an exported package: instructions, references, citations, smoke queries, and verification metadata.

A repo agent is a product view over a repository source: resource state, Context Packs, exports, review findings, and runtime usage.

Importing a repo does not magically create an autonomous engineer. It gives agents a better evidence layer.

## MCP is a runtime channel

MCP is how agents ask SourceBrief for context. It is not the core product value by itself.

The value is that SourceBrief can answer from reviewed, versioned, permission-scoped evidence. MCP makes that evidence available to agent clients.

## Production actions are out of scope

SourceBrief provides context. It does not execute production mutations. If an agent needs to deploy, restart services, write to GitHub, or touch production systems, keep those actions behind separate typed tools, approval boundaries, and rollback workflows.
