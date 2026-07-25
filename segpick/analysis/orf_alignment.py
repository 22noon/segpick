from __future__ import annotations

from Bio.Align import PairwiseAligner, substitution_matrices

from segpick.analysis.orf import calculate_orf_metrics
from segpick.models import ORFAlignmentMetrics, Sample


def _protein_aligner() -> PairwiseAligner:
    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -10.0
    aligner.extend_gap_score = -0.5
    return aligner



def _render_alignment(candidate_protein: str, reference_protein: str, alignment):
    candidate_blocks, reference_blocks = alignment.aligned
    candidate_parts: list[str] = []
    reference_parts: list[str] = []
    gap_lengths: list[int] = []
    candidate_pos = 0
    reference_pos = 0

    for candidate_block, reference_block in zip(candidate_blocks, reference_blocks, strict=True):
        candidate_start, candidate_end = map(int, candidate_block)
        reference_start, reference_end = map(int, reference_block)

        candidate_gap = candidate_start - candidate_pos
        reference_gap = reference_start - reference_pos
        width = max(candidate_gap, reference_gap)
        if width:
            candidate_parts.append(candidate_protein[candidate_pos:candidate_start].ljust(width, "-"))
            reference_parts.append(reference_protein[reference_pos:reference_start].ljust(width, "-"))
            if candidate_pos and reference_pos:
                gap_lengths.append(width)

        candidate_parts.append(candidate_protein[candidate_start:candidate_end])
        reference_parts.append(reference_protein[reference_start:reference_end])
        candidate_pos = candidate_end
        reference_pos = reference_end

    candidate_tail = candidate_protein[candidate_pos:]
    reference_tail = reference_protein[reference_pos:]
    width = max(len(candidate_tail), len(reference_tail))
    if width:
        candidate_parts.append(candidate_tail.ljust(width, "-"))
        reference_parts.append(reference_tail.ljust(width, "-"))

    aligned_candidate = "".join(candidate_parts)
    aligned_reference = "".join(reference_parts)
    match_line = "".join(
        "|" if candidate == reference else " " if "-" in (candidate, reference) else "."
        for candidate, reference in zip(aligned_candidate, aligned_reference, strict=True)
    )
    return aligned_candidate, aligned_reference, match_line, gap_lengths

def align_orf_proteins(
    candidate_protein: str,
    reference_protein: str,
    *,
    reference_id: str,
) -> ORFAlignmentMetrics:
    """Globally align two proteins and return transparent alignment metrics."""

    if not candidate_protein:
        raise ValueError("candidate_protein must not be empty")
    if not reference_protein:
        raise ValueError("reference_protein must not be empty")

    alignment = _protein_aligner().align(
        candidate_protein,
        reference_protein,
    )[0]
    candidate_blocks, reference_blocks = alignment.aligned
    aligned_candidate, aligned_reference, match_line, gap_lengths = _render_alignment(
        candidate_protein, reference_protein, alignment
    )

    aligned_residues = 0
    identical_residues = 0
    for candidate_block, reference_block in zip(
        candidate_blocks,
        reference_blocks,
        strict=True,
    ):
        candidate_start, candidate_end = map(int, candidate_block)
        reference_start, reference_end = map(int, reference_block)
        candidate_segment = candidate_protein[candidate_start:candidate_end]
        reference_segment = reference_protein[reference_start:reference_end]
        aligned_residues += len(candidate_segment)
        identical_residues += sum(
            candidate_residue == reference_residue
            for candidate_residue, reference_residue in zip(
                candidate_segment,
                reference_segment,
                strict=True,
            )
        )

    first_reference_start = int(reference_blocks[0][0])
    last_reference_end = int(reference_blocks[-1][1])
    internal_gap_residues = 0
    for index in range(1, len(candidate_blocks)):
        internal_gap_residues += int(
            candidate_blocks[index][0] - candidate_blocks[index - 1][1]
        )
        internal_gap_residues += int(
            reference_blocks[index][0] - reference_blocks[index - 1][1]
        )

    candidate_length = len(candidate_protein)
    reference_length = len(reference_protein)
    return ORFAlignmentMetrics(
        reference_id=reference_id,
        candidate_protein_length=candidate_length,
        reference_protein_length=reference_length,
        aligned_residues=aligned_residues,
        identical_residues=identical_residues,
        amino_acid_identity=identical_residues / aligned_residues,
        candidate_coverage=aligned_residues / candidate_length,
        reference_coverage=aligned_residues / reference_length,
        length_ratio=candidate_length / reference_length,
        n_terminal_missing=first_reference_start,
        c_terminal_missing=reference_length - last_reference_end,
        internal_gap_residues=internal_gap_residues,
        internal_gap_events=len(gap_lengths),
        largest_internal_gap=max(gap_lengths, default=0),
        aligned_candidate=aligned_candidate,
        aligned_reference=aligned_reference,
        match_line=match_line,
    )


def attach_orf_alignment_metrics(sample: Sample) -> None:
    """Compare each candidate ORF with the ORF of its BLAST reference."""

    reference_orfs: dict[str, str | None] = {}

    for gene in sample.genes.values():
        references = {reference.accession: reference for reference in gene.references}
        for candidate in gene.candidates:
            candidate.analysis.orf_alignment = None
            candidate_orf = candidate.analysis.orf
            blastx = candidate.analysis.blastx
            if blastx is not None and blastx.subject_protein:
                reference_id = blastx.subject_id
                reference_protein = blastx.subject_protein
            else:
                reference_id = candidate.blast_reference
                reference = references.get(reference_id) if reference_id else None
                if reference is None:
                    continue
                if reference.accession not in reference_orfs:
                    metrics = calculate_orf_metrics(reference.record.seq)
                    reference_orfs[reference.accession] = (
                        metrics.best_orf.protein if metrics.best_orf else None
                    )
                reference_protein = reference_orfs[reference.accession]

            if candidate_orf is None or candidate_orf.best_orf is None or not reference_protein:
                continue

            candidate.analysis.orf_alignment = align_orf_proteins(
                candidate_orf.best_orf.protein,
                reference_protein,
                reference_id=reference_id,
            )
