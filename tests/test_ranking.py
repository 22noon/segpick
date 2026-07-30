from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    CandidateContig,
    ContainmentMetrics,
    ContigMetadata,
    Gene,
)
from segpick.scoring import ScoringWeights, rank_gene


def make_candidate(
    candidate_id: str,
    *,
    length: int,
    confidence: float,
    z: float | None = 0.0,
    query_coverage: float = 1.0,
    anchor_coverage: float = 1.0,
    identity: float = 1.0,
    fragmentation: float = 0.0,
) -> CandidateContig:
    candidate = CandidateContig(
        id=candidate_id,
        record=SeqRecord(
            Seq("A" * length),
            id=candidate_id,
        ),
        metadata=ContigMetadata(
            segment="2",
            score=1.0,
            confidence=confidence,
            cluster="A",
            z=z,
        ),
    )

    candidate.analysis.containment = ContainmentMetrics(
        query_length=length,
        anchor_length=length,
        query_coverage=query_coverage,
        anchor_coverage=anchor_coverage,
        identity=identity,
        fragmentation=fragmentation,
    )

    return candidate


def test_rank_gene_selects_highest_score() -> None:
    gene = Gene(name="VP2", segment="2")

    strong = make_candidate(
        "strong",
        length=100,
        confidence=100,
        query_coverage=1.0,
        anchor_coverage=1.0,
        identity=1.0,
        fragmentation=0.0,
    )
    weak = make_candidate(
        "weak",
        length=100,
        confidence=50,
        query_coverage=0.5,
        anchor_coverage=0.5,
        identity=0.8,
        fragmentation=0.4,
    )

    gene.add_candidate(strong)
    gene.add_candidate(weak)

    result = rank_gene(gene, ScoringWeights())

    assert result.recommended.candidate_id == "strong"
    assert result.candidates[0].score > result.candidates[1].score


def test_rank_gene_uses_confidence_as_first_tiebreak() -> None:
    gene = Gene(name="VP2", segment="2")

    first = make_candidate(
        "first",
        length=100,
        confidence=100,
    )
    second = make_candidate(
        "second",
        length=100,
        confidence=90,
    )

    gene.add_candidate(first)
    gene.add_candidate(second)

    weights = ScoringWeights(
        protein_confidence=0,
        length_plausibility=1,
        containment=1,
        identity=1,
        fragmentation=1,
    )

    result = rank_gene(gene, weights)

    assert result.recommended.candidate_id == "first"


def test_rank_gene_uses_length_as_second_tiebreak() -> None:
    gene = Gene(name="VP2", segment="2")

    short = make_candidate(
        "short",
        length=100,
        confidence=100,
    )
    long = make_candidate(
        "long",
        length=120,
        confidence=100,
    )

    gene.add_candidate(short)
    gene.add_candidate(long)

    result = rank_gene(gene, ScoringWeights())

    assert result.recommended.candidate_id == "long"


def test_rank_gene_uses_id_as_final_tiebreak() -> None:
    gene = Gene(name="VP2", segment="2")

    beta = make_candidate(
        "beta",
        length=100,
        confidence=100,
    )
    alpha = make_candidate(
        "alpha",
        length=100,
        confidence=100,
    )

    gene.add_candidate(beta)
    gene.add_candidate(alpha)

    result = rank_gene(gene, ScoringWeights())

    assert result.recommended.candidate_id == "alpha"


def test_gene_without_candidates_cannot_be_ranked() -> None:
    gene = Gene(name="VP2", segment="2")

    try:
        rank_gene(gene, ScoringWeights())
    except ValueError as error:
        assert "no candidates" in str(error)
    else:
        raise AssertionError("Expected rank_gene to raise ValueError")
