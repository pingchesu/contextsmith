from datetime import UTC, datetime
from pathlib import Path

import pytest

from sourcebrief_shared.regression_proposal import (
    RegressionProposal,
    RegressionProposalError,
    load_reviewer_report,
    proposal_from_finding,
    proposals_from_report,
    select_finding,
    write_regression_proposal,
)
from sourcebrief_shared.review_findings import ReviewerFinding, build_reviewer_report

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "examples" / "self-improvement" / "reviewer-report-example.json"


def test_proposals_from_report_include_candidates_and_rejected_learning() -> None:
    report = load_reviewer_report(REPORT)
    proposals = proposals_from_report(report, owner="quality")

    assert len(proposals) == 4
    first = proposals[0]
    assert first.schema_version == "sourcebrief.regression-proposal.v1"
    assert first.source_report_id == report.report_id
    assert first.source_bundle_id == report.bundle_id
    assert first.status == "proposed"
    assert first.target_surface == "test"
    assert first.evidence_refs == ["cite-security-intro"]
    assert first.owner == "quality"
    rejected = proposals[-1]
    assert rejected.status == "rejected"
    assert rejected.source_finding_id == "finding-rejected-learning-nightly-optimizer"
    assert rejected.rationale.startswith("Rejected as durable learning")


def test_unsafe_mutation_finding_targets_runtime_pack() -> None:
    finding = ReviewerFinding(
        finding_id="finding-runtime-pack-silent-mutation",
        bundle_id="bundle-runtime-pack",
        severity="major",
        type="unsafe_mutation",
        summary="Generated runtime instruction implies silent self-improvement edits.",
        claim="The runtime pack may update itself from one reviewer opinion.",
        claim_ids=["claim-runtime-pack-silent-edit"],
        evidence_refs=["skill-section-self-improvement"],
        impact="Agents could treat a reviewer opinion as a permanent skill or prompt rule.",
        suggested_fix="Route runtime-pack wording changes through review proposal, validation gate, and staged adoption.",
        regression_candidate=True,
        confidence="high",
        reviewer_lens="safety",
        proposal_eligibility="candidate",
    )
    report = build_reviewer_report(
        report_id="report-runtime-pack",
        bundle_id="bundle-runtime-pack",
        reviewer_backend="local",
        reviewer_lenses=["safety"],
        generated_at=datetime.now(UTC),
        findings=[finding],
    )

    proposal = proposal_from_finding(report, finding, owner="runtime")

    assert proposal.target_surface == "runtime_pack"
    assert proposal.status == "proposed"
    assert proposal.claim_ids == ["claim-runtime-pack-silent-edit"]
    assert "staged adoption" in proposal.proposed_check


def test_select_finding_requires_candidate_or_rejected_learning() -> None:
    report = load_reviewer_report(REPORT)

    selected = select_finding(report, "finding-learning-quickstart-gap")
    assert selected.type == "quickstart_dx_failure"

    with pytest.raises(RegressionProposalError, match="finding not found"):
        select_finding(report, "missing")


def test_write_regression_proposal_artifact_round_trips(tmp_path: Path) -> None:
    report = load_reviewer_report(REPORT)
    finding = select_finding(report, "finding-major-overclaim")
    proposal = proposal_from_finding(report, finding, owner="docs")
    output = write_regression_proposal(tmp_path / "proposal.json", proposal)

    loaded = RegressionProposal.model_validate_json(output.read_text(encoding="utf-8"))
    assert loaded.proposal_id == "proposal-finding-major-overclaim"
    assert loaded.target_surface == "docs"
    assert loaded.acceptance
    assert loaded.bundle_refs == [report.bundle_id]
