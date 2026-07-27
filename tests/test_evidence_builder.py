import math
from segpick.read_support import attach_read_support

import pytest
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    CandidateContig,
    ContainmentMetrics,
    ContigMetadata,
)
from segpick.scoring import build_evidence, build_gene_evidence


def make_candidate(
    candidate_id: str,
    *,
    confidence: float,
    z: float | None,
    query_coverage: float,
    anchor_coverage: float,
    identity: float,
    fragmentation: float,
) -> CandidateContig:
    candidate = CandidateContig(
        id=candidate_id,
        record=SeqRecord(Seq("ATGC"), id=candidate_id),
        metadata=ContigMetadata(
            segment="2",
            score=1.0,
            confidence=confidence,
            cluster="A",
            z=z,
        ),
    )

    candidate.analysis.containment = ContainmentMetrics(
        query_length=4,
        anchor_length=4,
        query_coverage=query_coverage,
        anchor_coverage=anchor_coverage,
        identity=identity,
        fragmentation=fragmentation,
    )

    return candidate


def test_confidence_is_normalised_within_gene() -> None:
    first = make_candidate(
        "first",
        confidence=50,
        z=0,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0,
    )
    second = make_candidate(
        "second",
        confidence=100,
        z=0,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0,
    )

    evidence = build_gene_evidence([first, second])

    assert evidence["first"].protein_confidence == pytest.approx(0.5)
    assert evidence["second"].protein_confidence == pytest.approx(1.0)


def test_length_plausibility_uses_gaussian_penalty() -> None:
    candidate = make_candidate(
        "candidate",
        confidence=100,
        z=2.0,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0,
    )

    evidence = build_evidence(candidate, [candidate])

    assert evidence.length_plausibility == pytest.approx(
        math.exp(-2.0),
    )


def test_containment_combines_both_coverages() -> None:
    candidate = make_candidate(
        "candidate",
        confidence=100,
        z=0,
        query_coverage=0.8,
        anchor_coverage=0.5,
        identity=0.99,
        fragmentation=0,
    )

    evidence = build_evidence(candidate, [candidate])

    assert evidence.containment == pytest.approx(0.4)


def test_fragmentation_is_converted_to_positive_evidence() -> None:
    candidate = make_candidate(
        "candidate",
        confidence=100,
        z=0,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0.25,
    )

    evidence = build_evidence(candidate, [candidate])

    assert evidence.fragmentation == pytest.approx(0.75)


def test_missing_z_score_is_unavailable() -> None:
    candidate = make_candidate(
        "candidate",
        confidence=100,
        z=None,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0,
    )

    evidence = build_evidence(candidate, [candidate])

    assert evidence.length_plausibility is None


def test_zero_confidence_gene_is_handled() -> None:
    first = make_candidate(
        "first",
        confidence=0,
        z=0,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0,
    )
    second = make_candidate(
        "second",
        confidence=0,
        z=0,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0,
    )

    evidence = build_gene_evidence([first, second])

    assert evidence["first"].protein_confidence == 0.0
    assert evidence["second"].protein_confidence == 0.0

def test_read_support_is_unavailable_without_depth_metrics() -> None:
    candidate = make_candidate(
        "candidate",
        confidence=100,
        z=0,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0,
    )

    evidence = build_evidence(candidate, [candidate])

    assert evidence.coverage_sufficiency is None

def test_attached_read_support_becomes_evidence() -> None:
    candidate = make_candidate(
        "candidate",
        confidence=100,
        z=0,
        query_coverage=1,
        anchor_coverage=1,
        identity=1,
        fragmentation=0,
    )

    attach_read_support(
        candidate,
        {
            position: 10
            for position in range(1, candidate.length + 1)
        },
        minimum_terminal_bases=1,
    )

    evidence = build_evidence(candidate, [candidate])

    assert evidence.coverage_sufficiency == pytest.approx(1.0)
