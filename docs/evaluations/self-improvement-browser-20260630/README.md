# Self-improvement browser launch proof (#213)

Issue: [#213](https://github.com/pingchesu/sourcebrief/issues/213)
Parent: [#208](https://github.com/pingchesu/sourcebrief/issues/208)
Child finding: [#231](https://github.com/pingchesu/sourcebrief/issues/231)

## Verdict

**PASS for #213 UI/browser evidence, with one tracked setup finding.**

The `/self-improvement` product surface was browser-verified on the current launch stack after fixing the local proof-stack CORS origin. The page demonstrates the intended **artifact-first / dry-run / no-silent-mutation** boundary and should remain worded as a review/evidence surface, not as recurring autonomous learning that silently changes product behavior.

## Scope verified

- Signed into the web console as the launch proof admin.
- Opened `/self-improvement` from the sidebar.
- Verified initial empty/loading state:
  - page header: `Evidence-backed improvement loop`;
  - operating boundary: `No silent mutation: enforced by product contract`;
  - `Run MVP smoke` and `Run sleep dry-run` controls present;
  - empty review history before a run.
- Ran **MVP smoke** from the UI:
  - last run completed;
  - artifact metrics showed 5 records immediately after the MVP smoke run;
  - review history populated with bundle/report/proposal/gate/staged-adoption rows;
  - selected an artifact row and verified the redacted artifact detail panel.
- Ran **sleep dry-run** from the UI:
  - last run completed;
  - summary used `sourcebrief.sleep-replay-summary.v1`;
  - `dry_run: true`;
  - candidate proposals were produced as review artifacts, not applied product mutations.
- Re-loaded the page after the dry-run and confirmed durable history via API summary:
  - 7 records total;
  - 2 gate results / 2 proposals / 1 bundle / 1 report / 1 staged-adoption receipt;
  - `no_silent_mutation: true`.

## Browser / network finding

First browser login attempt failed with `TypeError: Failed to fetch`; API logs showed the CORS preflight for login returned `400 Bad Request`. The evidence stack had been rebuilt on random ports and API CORS did not include the active web origin.

This was fixed for the proof run by restarting only the isolated local API/worker services with the active web origin in `SOURCEBRIEF_CORS_ORIGINS`. The failure is tracked as [#231](https://github.com/pingchesu/sourcebrief/issues/231) so future random-port browser proof stacks validate CORS before screenshot capture.

## Evidence files

| Artifact | Purpose | SHA-256 |
| --- | --- | --- |
| [`api-summary.redacted.json`](api-summary.redacted.json) | Redacted API summary of final self-improvement history after MVP smoke + sleep dry-run. | `41513964d9cd853615c486db9b63ccf585a56ca5b617fc944e6e0a55a9ea375b` |
| [`../../assets/screenshots/self-improvement-20260630/01-initial.redacted.png`](../../assets/screenshots/self-improvement-20260630/01-initial.redacted.png) | Initial page state: header, no-silent-mutation boundary, controls, empty history. | `f0b1ef25e0c780afdb2b9c1a9f84bff6c81a6c5c6eab4e72ad64bbce6f7dbeb7` |
| [`../../assets/screenshots/self-improvement-20260630/02-mvp-smoke.redacted.png`](../../assets/screenshots/self-improvement-20260630/02-mvp-smoke.redacted.png) | MVP smoke completed: 5 artifacts, 1 accepted gate, 1 blocker/major finding, review history rows. | `84143d4b2a6c97783d4d4ac58074773f79d312a293cb3cff5e214c5be02d64c3` |
| [`../../assets/screenshots/self-improvement-20260630/03-artifact-detail.redacted.png`](../../assets/screenshots/self-improvement-20260630/03-artifact-detail.redacted.png) | Selected artifact detail with kind/status chips and safe fixture proposal payload. | `ba2005346b532d59b026a4506f96e63a174ee4e9af29baf5339b5970ef870075` |
| [`../../assets/screenshots/self-improvement-20260630/04-sleep-dry-run.redacted.png`](../../assets/screenshots/self-improvement-20260630/04-sleep-dry-run.redacted.png) | Sleep dry-run proof context: dry-run flow and resulting history rows. | `78379a8d525b2b5c88cd0bea7a95fcc9a3d081e7ac2ad65def21a34c4657c25f` |

Screenshot redactions intentionally mask local artifact roots, workspace/project IDs, and raw run payload blocks while preserving visible product-state evidence.

## Launch wording boundary

Allowed wording:

- "Self-improvement artifact loop has browser proof for MVP smoke, redacted history/detail, and sleep dry-run."
- "The surface is artifact-first and enforces a no-silent-mutation boundary."

Avoid / do not claim:

- "Recurring autonomous learning is live."
- "Sleep/replay applies lessons automatically."
- "Staged receipts are production changes."
