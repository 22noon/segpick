from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import pytest

from segpick.models import (
    CandidateContig,
    ContainmentMetrics,
    ContigMetadata,
    Gene,
)
from segpick.reporting.view_models import build_gene_page_view
from segpick.scoring import ScoringWeights, rank_gene


def make_candidate(
    candidate_id: str,
    confidence: float,
) -> CandidateContig:
    candidate = CandidateContig(
        id=candidate_id,
        record=SeqRecord(
            Seq("A" * 100),
            id=candidate_id,
        ),
        metadata=ContigMetadata(
            segment="2",
            score=1.0,
            confidence=confidence,
            cluster="A",
            z=0.0,
        ),
    )

    candidate.analysis.containment = ContainmentMetrics(
        query_length=100,
        anchor_length=100,
        query_coverage=1.0,
        anchor_coverage=1.0,
        identity=0.99,
        fragmentation=0.0,
        structural_score=0.99,
        status="COMPLETE",
    )

    return candidate


def test_build_gene_page_view() -> None:
    gene = Gene(name="VP2", segment="2")
    gene.add_candidate(make_candidate("contig_a", 100))
    gene.add_candidate(make_candidate("contig_b", 50))

    recommendation = rank_gene(
        gene,
        ScoringWeights(),
    )

    view = build_gene_page_view(
        gene,
        recommendation,
    )

    assert view.gene == "VP2"
    assert view.recommendation is not None
    assert view.recommendation.candidate_id == "contig_a"
    assert len(view.candidates) == 2
    assert view.candidates[0].recommended is True
    assert view.recommendation.evidence
    assert {
        item.name
        for item in view.recommendation.evidence
    } == {
        "protein_confidence",
        "length_plausibility",
        "containment",
        "identity",
        "fragmentation",
    }
    evidence_by_name = {
    item.name: item
    for item in view.recommendation.evidence
    }

    protein = evidence_by_name["protein_confidence"]

    assert protein.value is not None
    assert protein.contribution is not None
    assert protein.effective_weight is not None

    assert sum(
        item.contribution
        for item in view.recommendation.evidence
        if item.contribution is not None
    ) == pytest.approx(view.recommendation.score)
