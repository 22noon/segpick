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
from segpick.read_support import attach_read_support


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

    assert view.recommendation.runner_up_id == "contig_b"
    assert view.recommendation.runner_up_score is not None
    assert view.recommendation.score_gap is not None
    assert view.recommendation.runner_up_strength in {
        "close",
        "secondary",
        "weak",
    }

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
        "read_support",
        "orf_quality",
    }

    evidence_by_name = {
    item.name: item
    for item in view.recommendation.evidence
    }

    assert evidence_by_name["read_support"].value is None
    assert evidence_by_name["read_support"].contribution is None
    assert evidence_by_name["read_support"].effective_weight is None

    protein = evidence_by_name["protein_confidence"]

    assert protein.value is not None
    assert protein.contribution is not None
    assert protein.effective_weight is not None

    assert sum(
        item.contribution
        for item in view.recommendation.evidence
        if item.contribution is not None
    ) == pytest.approx(view.recommendation.score)

def test_gene_page_view_contains_attached_read_support() -> None:
    gene = Gene(name="VP2", segment="2")
    candidate = make_candidate("contig_a", 100)

    attach_read_support(
        candidate,
        {
            position: 10
            for position in range(1, candidate.length + 1)
        },
        minimum_terminal_bases=1,
    )

    gene.add_candidate(candidate)

    recommendation = rank_gene(
        gene,
        ScoringWeights(),
    )

    view = build_gene_page_view(
        gene,
        recommendation,
    )

    candidate_view = view.candidates[0]

    assert candidate_view.read_support.available is True
    assert candidate_view.read_support.mean_depth == pytest.approx(10.0)
    assert candidate_view.read_support.covered_fraction == pytest.approx(1.0)
    assert candidate_view.read_support.overall_support == pytest.approx(1.0)

def test_gene_page_view_marks_missing_read_support() -> None:
    gene = Gene(name="VP2", segment="2")
    gene.add_candidate(make_candidate("contig_a", 100))

    recommendation = rank_gene(
        gene,
        ScoringWeights(),
    )

    view = build_gene_page_view(
        gene,
        recommendation,
    )

    read_support = view.candidates[0].read_support

    assert read_support.available is False
    assert read_support.mean_depth is None
    assert read_support.overall_support is None
    
def test_runner_up_is_marked_weak_when_score_gap_is_large() -> None:
    gene = Gene(name="VP2", segment="2")

    strong = make_candidate("strong", 100)
    weak = make_candidate("weak", 1)

    weak.analysis.containment.query_coverage = 0.2
    weak.analysis.containment.anchor_coverage = 0.2
    weak.analysis.containment.identity = 0.5
    weak.analysis.containment.fragmentation = 0.8

    gene.add_candidate(strong)
    gene.add_candidate(weak)

    recommendation = rank_gene(gene, ScoringWeights())
    view = build_gene_page_view(gene, recommendation)

    assert view.recommendation is not None
    assert view.recommendation.runner_up_id == "weak"
    assert view.recommendation.runner_up_strength == "weak"
