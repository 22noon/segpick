from segpick.analysis.orf_alignment import align_orf_proteins
from segpick.analysis.protein_interpretation import interpret_protein_alignment


def test_interpretation_marks_intact_protein():
    alignment = align_orf_proteins(
        "MABCDE",
        "MABCDE",
        reference_id="reference",
    )

    interpretation = interpret_protein_alignment(alignment)

    assert interpretation.structural_status == "intact"
    assert interpretation.terminal_status == "complete"
    assert interpretation.internal_indel_pattern == "none"
    assert interpretation.possible_frameshift_pattern is False
    assert interpretation.summary == "Full-length protein recovered with no internal indels."


def test_interpretation_marks_terminal_truncation_and_deletion():
    alignment = align_orf_proteins(
        "MABCDE",
        "XXMABQQQCDEYY",
        reference_id="reference",
    )

    interpretation = interpret_protein_alignment(alignment)

    assert interpretation.structural_status == "truncated_with_indels"
    assert interpretation.terminal_status == "both_terminal_truncation"
    assert interpretation.internal_indel_pattern == "single_deletion"
    assert any("N-terminal truncation" in item for item in interpretation.findings)
    assert any("Internal deletion" in item for item in interpretation.findings)


def test_interpretation_flags_scattered_small_indels_as_possible_frameshift():
    from segpick.models import ORFAlignmentMetrics

    alignment = ORFAlignmentMetrics(
        reference_id="reference",
        candidate_protein_length=100,
        reference_protein_length=100,
        aligned_residues=97,
        identical_residues=95,
        amino_acid_identity=95 / 97,
        candidate_coverage=0.97,
        reference_coverage=0.97,
        length_ratio=1.0,
        n_terminal_missing=0,
        c_terminal_missing=0,
        internal_gap_residues=3,
        internal_gap_events=3,
        largest_internal_gap=1,
        internal_insertion_residues=2,
        internal_insertion_events=2,
        largest_internal_insertion=1,
        internal_deletion_residues=1,
        internal_deletion_events=1,
        largest_internal_deletion=1,
    )

    interpretation = interpret_protein_alignment(alignment)

    assert interpretation.structural_status == "complex"
    assert interpretation.internal_indel_pattern == "multiple_indels"
    assert interpretation.possible_frameshift_pattern is True
    assert any("possible frameshift" in item for item in interpretation.findings)
