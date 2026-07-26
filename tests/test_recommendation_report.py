from segpick.models import ProteinContinuity
from segpick.scoring import (
    EvidenceAgreement,
    build_recommendation_report,
)


def test_report_summarises_support_without_manual_review():
    agreement = EvidenceAgreement(
        channel_winners={
            "protein_confidence": ("contig_a",),
            "blastx_consistency": ("contig_a",),
        },
        supporting_channels=("protein_confidence", "blastx_consistency"),
        disagreeing_channels=(),
        strong_conflicts=(),
        agreement_fraction=1.0,
        confidence="high",
    )

    report = build_recommendation_report("contig_a", agreement)

    assert report.manual_review is False
    assert report.confidence == "high"
    assert report.opposing_evidence == ()
    assert "ORF–BLASTX consistency" in report.supporting_evidence[1]
    assert "no major conflicts" in report.summary


def test_report_requests_review_for_strong_structural_conflict():
    agreement = EvidenceAgreement(
        channel_winners={
            "protein_confidence": ("contig_a",),
            "blastx_consistency": ("contig_b",),
        },
        supporting_channels=("protein_confidence",),
        disagreeing_channels=("blastx_consistency",),
        strong_conflicts=("blastx_consistency",),
        agreement_fraction=0.5,
        confidence="low",
    )

    report = build_recommendation_report("contig_a", agreement)

    assert report.manual_review is True
    assert report.opposing_evidence == (
        "ORF–BLASTX consistency favours contig_b.",
    )
    assert report.evidence_conflicts == (
        "Strong structural evidence from ORF–BLASTX consistency favours contig_b.",
    )
    assert "manual review" in report.summary


def test_report_serialises_as_plain_data():
    agreement = EvidenceAgreement(
        channel_winners={"containment": ("a", "b")},
        supporting_channels=("containment",),
        disagreeing_channels=(),
        strong_conflicts=(),
        agreement_fraction=1.0,
        confidence="high",
    )

    report = build_recommendation_report("a", agreement)

    assert report.to_dict()["supporting_evidence"] == [
        "Containment supports the recommended candidate."
    ]


def test_report_requests_review_for_complementary_fragments():
    agreement = EvidenceAgreement(
        channel_winners={"protein_confidence": ("contig_a",)},
        supporting_channels=("protein_confidence",),
        disagreeing_channels=(),
        strong_conflicts=(),
        agreement_fraction=1.0,
        confidence="high",
    )
    continuity = ProteinContinuity(
        classification="complementary_fragments",
        candidate_count=2,
        combined_coverage=0.98,
        best_single_coverage=0.55,
        complementary_candidate_ids=("contig_a", "contig_b"),
        redundant_overlap=False,
        uncovered_regions=(),
        summary="Multiple candidates collectively span most of the expected protein.",
        findings=(),
    )

    report = build_recommendation_report("contig_a", agreement, continuity)

    assert report.manual_review is True
    assert report.assembly_review_required is True
    assert report.confidence == "low"
    assert "selecting one contig" in report.assembly_level_evidence[0]
    assert "distributed across multiple contigs" in report.summary


def test_report_notes_redundant_overlap_without_forcing_review():
    agreement = EvidenceAgreement(
        channel_winners={"protein_confidence": ("contig_a",)},
        supporting_channels=("protein_confidence",),
        disagreeing_channels=(),
        strong_conflicts=(),
        agreement_fraction=1.0,
        confidence="high",
    )
    continuity = ProteinContinuity(
        classification="complete_single_candidate",
        candidate_count=2,
        combined_coverage=1.0,
        best_single_coverage=0.95,
        complementary_candidate_ids=(),
        redundant_overlap=True,
        uncovered_regions=(),
        summary="At least one candidate spans most of the expected protein length.",
        findings=(),
    )

    report = build_recommendation_report("contig_a", agreement, continuity)

    assert report.manual_review is False
    assert report.assembly_review_required is False
    assert "overlapping protein regions" in report.assembly_level_evidence[0]


def _convergence(strength: str):
    from segpick.models import EvidenceConvergence, ObservationInterval

    protein = ObservationInterval(
        coordinate_system="reference_protein:ref1",
        start=214,
        end=217,
        observation_type="internal_deletion",
        source="protein_alignment",
        description="Internal deletion at AA 214-217.",
    )
    coverage = ObservationInterval(
        coordinate_system="reference_protein:ref1",
        start=213,
        end=221,
        observation_type="coverage_drop",
        source="read_coverage",
        description="Sustained coverage drop at AA 213-221.",
    )
    return EvidenceConvergence(
        coordinate_system="reference_protein:ref1",
        start=213,
        end=221,
        strength=strength,
        sources=("protein_alignment", "read_coverage"),
        observation_types=("coverage_drop", "internal_deletion"),
        observations=(protein, coverage),
        summary="2 independent evidence sources converge on reference-protein positions 213-221.",
        candidate_id="contig_a",
    )


def test_moderate_convergence_is_reported_without_forcing_review():
    agreement = EvidenceAgreement(
        channel_winners={"protein_confidence": ("contig_a",)},
        supporting_channels=("protein_confidence",),
        disagreeing_channels=(),
        strong_conflicts=(),
        agreement_fraction=1.0,
        confidence="high",
    )

    report = build_recommendation_report(
        "contig_a",
        agreement,
        convergences=(_convergence("moderate"),),
    )

    assert report.manual_review is False
    assert report.convergence_review_required is False
    assert "positions 213-221" in report.convergence_evidence[0]


def test_strong_convergence_requires_manual_review():
    agreement = EvidenceAgreement(
        channel_winners={"protein_confidence": ("contig_a",)},
        supporting_channels=("protein_confidence",),
        disagreeing_channels=(),
        strong_conflicts=(),
        agreement_fraction=1.0,
        confidence="high",
    )

    report = build_recommendation_report(
        "contig_a",
        agreement,
        convergences=(_convergence("strong"),),
    )

    assert report.manual_review is True
    assert report.convergence_review_required is True
    assert report.confidence == "low"
    assert "strong local evidence convergence" in report.summary
