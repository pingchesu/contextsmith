# Self-improvement browser launch proof (#213)

Issue: #213
Parent: #208
Resolved setup findings: #231, #237

## Verdict

**PASS for #213 UI/browser evidence, with resolved setup findings.**

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
  - the UI completed the dry-run flow and added sleep proposal/gate artifacts to review history;
  - candidate proposals were produced as review artifacts, not applied product mutations;
  - final API summary shows 7 records total and `no_silent_mutation: true`.
- Re-loaded the page after the dry-run and confirmed durable history via API summary:
  - 7 records total;
  - 2 gate results / 2 proposals / 1 bundle / 1 report / 1 staged-adoption receipt;
  - `no_silent_mutation: true`.

## Browser / network finding

First browser login attempt failed with `TypeError: Failed to fetch`; API logs showed the CORS preflight for login returned `400 Bad Request`. The evidence stack had been rebuilt on random ports and API CORS did not include the active web origin.

This was fixed for the proof run by restarting only the isolated local API/worker services with the active web origin in `SOURCEBRIEF_CORS_ORIGINS`. The launch/browser proof runner now validates the active web origin before screenshot capture so future random-port browser proof stacks fail fast instead of producing browser CORS noise.

## Evidence files

| Artifact | Purpose | SHA-256 |
| --- | --- | --- |
| [`api-summary.redacted.json`](api-summary.redacted.json) | Redacted API summary of final self-improvement history after MVP smoke + sleep dry-run. | `41513964d9cd853615c486db9b63ccf585a56ca5b617fc944e6e0a55a9ea375b` |
| [`../../assets/screenshots/self-improvement-20260630/01-initial.redacted.png`](../../assets/screenshots/self-improvement-20260630/01-initial.redacted.png) | Initial page state: header, no-silent-mutation boundary, controls, empty history. | `a523638ab477f806ab6dde7bf0aa03ff5d0974f2348ed5ea2f3558851c0eed1a` |
| [`../../assets/screenshots/self-improvement-20260630/02-mvp-smoke.redacted.png`](../../assets/screenshots/self-improvement-20260630/02-mvp-smoke.redacted.png) | MVP smoke completed: 5 artifacts, 1 accepted gate, 1 blocker/major finding, review history rows. | `e1436153ea2df792621652b7396134e4f821475a3ac86d164a9b248884e9d73e` |
| [`../../assets/screenshots/self-improvement-20260630/03-artifact-detail.redacted.png`](../../assets/screenshots/self-improvement-20260630/03-artifact-detail.redacted.png) | Selected artifact detail with kind/status chips and safe fixture proposal payload. | `0d76de909dae258e0ea8b61230466be9a9f3b9c07a917c5845c8f8ba1a93dda8` |
| [`../../assets/screenshots/self-improvement-20260630/04-sleep-dry-run.redacted.png`](../../assets/screenshots/self-improvement-20260630/04-sleep-dry-run.redacted.png) | Sleep dry-run proof context: dry-run flow and resulting history rows. | `67a8a199e1f6c8c789993d94cf64052262a2061a50b6e611e7f350f5dc170af0` |

Screenshot redactions intentionally mask local artifact roots, workspace/project IDs, and raw run payload blocks while preserving visible product-state evidence.

## Launch wording boundary

Allowed wording:

- "Self-improvement artifact loop has browser proof for MVP smoke, redacted history/detail, and sleep dry-run."
- "The surface is artifact-first and enforces a no-silent-mutation boundary."

Avoid / do not claim:

- "Recurring autonomous learning is live."
- "Sleep/replay applies lessons automatically."
- "Staged receipts are production changes."
