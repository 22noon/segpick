from Bio.Seq import Seq

from segpick.analysis.orf import calculate_orf_metrics, find_orfs


def test_finds_complete_forward_orf() -> None:
    sequence = "CCCATG" + ("GCT" * 25) + "TAAACC"

    hits = find_orfs(sequence, minimum_protein_length=20)

    best = hits[0]
    assert best.strand == "+"
    assert best.start == 3
    assert best.end == 84
    assert best.protein_length == 26
    assert best.complete is True


def test_finds_complete_reverse_orf() -> None:
    coding = Seq("ATG" + ("GCT" * 25) + "TAA")
    sequence = "CCC" + str(coding.reverse_complement()) + "GGG"

    hits = find_orfs(sequence, minimum_protein_length=20)

    reverse_hits = [hit for hit in hits if hit.strand == "-" and hit.complete]
    assert reverse_hits
    best = reverse_hits[0]
    assert best.start == 3
    assert best.end == 84
    assert best.protein_length == 26


def test_reports_partial_orf_without_stop_codon() -> None:
    sequence = "ATG" + ("GCT" * 25)

    metrics = calculate_orf_metrics(sequence, minimum_protein_length=20)

    assert metrics.best_orf is not None
    assert metrics.best_orf.has_start_codon is True
    assert metrics.best_orf.has_stop_codon is False
    assert metrics.complete is False
    assert metrics.protein_length == 26


def test_can_exclude_partial_orfs() -> None:
    sequence = "ATG" + ("GCT" * 25)

    metrics = calculate_orf_metrics(
        sequence,
        minimum_protein_length=20,
        include_partial=False,
    )

    assert metrics.best_orf is None
    assert metrics.orf_count == 0


def test_rejects_negative_minimum_length() -> None:
    try:
        find_orfs("ATGTAA", minimum_protein_length=-1)
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
