from __future__ import annotations

import pytest
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    CandidateContig,
    ContigMetadata,
    Gene,
)
from segpick.read_support import (
    attach_gene_depths,
    attach_read_support,
)


def make_candidate(
    candidate_id: str,
    length: int = 100,
) -> CandidateContig:
    return CandidateContig(
        id=candidate_id,
        record=SeqRecord(
            Seq("A" * length),
            id=candidate_id,
        ),
        metadata=ContigMetadata(
            segment="2",
            score=1.0,
            confidence=100.0,
            cluster="A",
            z=0.0,
        ),
    )


def test_attach_read_support_to_candidate() -> None:
    candidate = make_candidate("contig_a", length=100)

    metrics = attach_read_support(
        candidate,
        {
            position: 10
            for position in range(1, 101)
        },
        minimum_terminal_bases=10,
    )

    assert candidate.analysis.read_support is metrics
    assert metrics.read_support == pytest.approx(1.0)


def test_attach_gene_depths_matches_candidate_ids() -> None:
    gene = Gene(name="VP2", segment="2")
    first = make_candidate("contig_a")
    second = make_candidate("contig_b")

    gene.add_candidate(first)
    gene.add_candidate(second)

    attached = attach_gene_depths(
        gene,
        {
            "contig_a": {
                position: 10
                for position in range(1, 101)
            }
        },
        minimum_terminal_bases=10,
    )

    assert set(attached) == {"contig_a"}
    assert first.analysis.read_support is not None
    assert second.analysis.read_support is None


def test_attach_gene_depths_strict_mode_rejects_missing_data() -> None:
    gene = Gene(name="VP2", segment="2")
    gene.add_candidate(make_candidate("contig_a"))

    with pytest.raises(
        KeyError,
        match="No depth data found",
    ):
        attach_gene_depths(
            gene,
            {},
            strict=True,
        )
