# EvoEmbedding temporal-memory 50Q eval

This directory contains a structured SourceBrief eval manifest for deciding whether EvoEmbedding-style temporal retrieval is worth adopting.

- Manifest: `eval_manifest.json`
- Schema: `sourcebrief.eval-manifest.v1`
- Question count: 50
- Negative controls: 6
- Companion plan: [`../../docs/EVOEMBEDDING_EVALUATION_PLAN.md`](../../docs/EVOEMBEDDING_EVALUATION_PLAN.md)

The manifest intentionally uses normalized placeholder IDs. Before running it against `/retrieval-evals`, replace workspace/project/resource/snapshot placeholders with the real imported SourceBrief docs, self-improvement docs, evaluation artifacts, EvoEmbedding repo, and operator-curated thread notes.

The current intended use is evaluation design and later profile-matrix execution, not evidence that EvoEmbedding has already been adopted.
