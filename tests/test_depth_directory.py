from __future__ import annotations

import pytest
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    CandidateContig,
    ContigMetadata,
    Gene,
    Sample,
)
from segpick.read_support import (
    attach_depth_directory,
    attached_read_support,
    candidate_depth_path,
)


def make_candidate(
    candidate_id: str,
    length: int = 10,
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


def make_sample() -> Sample:
    gene = Gene(name="VP2", segment="2")
    gene.add_candidate(make_candidate("contig_a"))
    gene.add_candidate(make_candidate("contig_b"))

    sample = Sample(name="sample")
    sample.add_gene(gene)

    return sample


def write_uniform_depth(
    path,
    sequence_id: str,
    length: int = 10,
    depth: int = 10,
) -> None:
    path.write_text(
        "".join(
            f"{sequence_id}\t{position}\t{depth}\n"
            for position in range(1, length + 1)
        )
    )


def test_candidate_depth_path() -> None:
    path = candidate_depth_path(
        "depth",
        "contig_a",
        suffix=".depth.txt",
    )

    assert path.name == "contig_a.depth.txt"


def test_attach_depth_directory(tmp_path) -> None:
    sample = make_sample()

    write_uniform_depth(
        tmp_path / "contig_a.depth.txt",
        "contig_a",
    )
    write_uniform_depth(
        tmp_path / "contig_b.depth.txt",
        "contig_b",
    )

    summary = attach_depth_directory(
        sample,
        tmp_path,
        minimum_terminal_bases=1,
    )

    assert summary.candidate_count == 2
    assert summary.files_found == 2
    assert summary.files_missing == 0
    assert summary.metrics_attached == 2

    attached = attached_read_support(sample)

    assert set(attached) == {
        "contig_a",
        "contig_b",
    }
    assert attached["contig_a"].read_support == pytest.approx(1.0)


def test_missing_files_are_skipped_by_default(tmp_path) -> None:
    sample = make_sample()

    write_uniform_depth(
        tmp_path / "contig_a.depth.txt",
        "contig_a",
    )

    summary = attach_depth_directory(
        sample,
        tmp_path,
        minimum_terminal_bases=1,
    )

    assert summary.files_found == 1
    assert summary.files_missing == 1
    assert summary.missing_candidates == ("contig_b",)

    assert (
        sample.genes["VP2"]
        .candidates[1]
        .analysis.read_support
        is None
    )


def test_strict_mode_rejects_missing_file(tmp_path) -> None:
    sample = make_sample()

    with pytest.raises(
        FileNotFoundError,
        match="contig_a",
    ):
        attach_depth_directory(
            sample,
            tmp_path,
            strict=True,
        )


def test_single_sequence_file_can_use_different_sequence_label(
    tmp_path,
) -> None:
    sample = make_sample()

    write_uniform_depth(
        tmp_path / "contig_a.depth.txt",
        "alternative_label",
    )

    summary = attach_depth_directory(
        sample,
        tmp_path,
        minimum_terminal_bases=1,
    )

    assert summary.metrics_attached == 1
    assert (
        sample.genes["VP2"]
        .candidates[0]
        .analysis.read_support
        is not None
    )


def test_multi_sequence_file_requires_matching_candidate_id(
    tmp_path,
) -> None:
    sample = make_sample()

    path = tmp_path / "contig_a.depth.txt"
    path.write_text(
        "other_a\t1\t10\n"
        "other_b\t1\t10\n"
    )

    with pytest.raises(
        KeyError,
        match="does not contain candidate",
    ):
        attach_depth_directory(
            sample,
            tmp_path,
        )
