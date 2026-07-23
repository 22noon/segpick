import pytest

from segpick.analysis.orf import calculate_orf_metrics
from segpick.analysis.orf_alignment import align_orf_proteins
from segpick.analysis.orf_quality import calculate_orf_quality


def test_complete_matching_orf_has_full_quality():
    orf = calculate_orf_metrics("ATGAAACCCGGGTAA", minimum_protein_length=1)
    alignment = align_orf_proteins(
        orf.best_orf.protein,
        orf.best_orf.protein,
        reference_id="ref",
    )

    quality = calculate_orf_quality(orf, alignment)

    assert quality is not None
    assert quality.score == pytest.approx(1.0)
    assert quality.complete_orf == 1.0
    assert quality.protein_identity == pytest.approx(1.0)
    assert quality.terminal_completeness == pytest.approx(1.0)


def test_quality_redistributes_weight_without_reference_alignment():
    orf = calculate_orf_metrics("ATGAAACCCGGGTAA", minimum_protein_length=1)

    quality = calculate_orf_quality(orf, None)

    assert quality is not None
    assert quality.score == pytest.approx(1.0)
    assert quality.protein_identity is None
    assert quality.reference_coverage is None


def test_partial_orf_is_penalised_without_reference_alignment():
    orf = calculate_orf_metrics("ATGAAACCCGGG", minimum_protein_length=1)

    quality = calculate_orf_quality(orf, None)

    assert quality is not None
    assert quality.complete_orf == 0.0
    assert quality.start_codon == 1.0
    assert quality.stop_codon == 0.0
    assert quality.score == pytest.approx(0.25)


def test_missing_orf_has_no_quality_metrics():
    orf = calculate_orf_metrics("AAA", minimum_protein_length=2)

    assert calculate_orf_quality(orf, None) is None
