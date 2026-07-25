from __future__ import annotations

from segpick.models import ORFAlignmentMetrics, ProteinInterpretation, Sample


def interpret_protein_alignment(
    alignment: ORFAlignmentMetrics,
) -> ProteinInterpretation:
    """Convert protein-alignment measurements into conservative interpretations."""

    n_missing = alignment.n_terminal_missing
    c_missing = alignment.c_terminal_missing
    indel_events = alignment.internal_gap_events

    if n_missing and c_missing:
        terminal_status = "both_terminal_truncation"
    elif n_missing:
        terminal_status = "n_terminal_truncation"
    elif c_missing:
        terminal_status = "c_terminal_truncation"
    else:
        terminal_status = "complete"

    if indel_events == 0:
        internal_indel_pattern = "none"
    elif indel_events == 1 and alignment.internal_deletion_events == 1:
        internal_indel_pattern = "single_deletion"
    elif indel_events == 1 and alignment.internal_insertion_events == 1:
        internal_indel_pattern = "single_insertion"
    else:
        internal_indel_pattern = "multiple_indels"

    possible_frameshift = (
        indel_events >= 3 and alignment.largest_internal_gap <= 3
    )

    findings: list[str] = []
    if n_missing:
        findings.append(
            f"N-terminal truncation: {n_missing} reference residues missing."
        )
    if c_missing:
        findings.append(
            f"C-terminal truncation: {c_missing} reference residues missing."
        )
    if alignment.internal_deletion_events:
        findings.append(
            f"Internal deletion: {alignment.internal_deletion_residues} residues "
            f"across {alignment.internal_deletion_events} event(s); largest "
            f"{alignment.largest_internal_deletion} aa."
        )
    if alignment.internal_insertion_events:
        findings.append(
            f"Internal insertion: {alignment.internal_insertion_residues} residues "
            f"across {alignment.internal_insertion_events} event(s); largest "
            f"{alignment.largest_internal_insertion} aa."
        )
    if possible_frameshift:
        findings.append(
            "Several small scattered indels form a pattern consistent with a "
            "possible frameshift or local assembly error."
        )

    if terminal_status == "complete" and indel_events == 0:
        structural_status = "intact"
        summary = "Full-length protein recovered with no internal indels."
    elif terminal_status != "complete" and indel_events == 0:
        structural_status = "truncated"
        summary = "Protein is terminally truncated but has no internal indels."
    elif possible_frameshift:
        structural_status = "complex"
        summary = "Multiple scattered protein differences warrant manual review."
    elif terminal_status != "complete":
        structural_status = "truncated_with_indels"
        summary = "Protein has terminal truncation and internal indel differences."
    else:
        structural_status = "internal_difference"
        summary = "Full-length protein recovered with internal indel differences."

    if not findings:
        findings.append("No terminal truncations or internal indels detected.")

    return ProteinInterpretation(
        structural_status=structural_status,
        terminal_status=terminal_status,
        internal_indel_pattern=internal_indel_pattern,
        possible_frameshift_pattern=possible_frameshift,
        summary=summary,
        findings=tuple(findings),
    )


def attach_protein_interpretations(sample: Sample) -> None:
    """Attach a protein interpretation wherever alignment metrics are available."""

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            alignment = candidate.analysis.orf_alignment
            candidate.analysis.protein_interpretation = (
                interpret_protein_alignment(alignment)
                if alignment is not None
                else None
            )
