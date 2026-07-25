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
