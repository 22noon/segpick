from __future__ import annotations

from segpick.analysis.orf_alignment import align_orf_proteins
from segpick.models import BlastXConsistency, BlastXHit, ORFHit, Sample


def _query_interval(hit: BlastXHit) -> tuple[int, int]:
    return min(hit.query_start, hit.query_end) - 1, max(hit.query_start, hit.query_end)


def _interval_coverage(orf: ORFHit, hit: BlastXHit) -> tuple[float, float]:
    hit_start, hit_end = _query_interval(hit)
    overlap = max(0, min(orf.end, hit_end) - max(orf.start, hit_start))
    hit_length = max(0, hit_end - hit_start)
    orf_length = max(0, orf.end - orf.start)
    return (
        overlap / hit_length if hit_length else 0.0,
        overlap / orf_length if orf_length else 0.0,
    )


def _signed_frame(orf: ORFHit) -> int:
    frame = orf.frame + 1
    return frame if orf.strand == "+" else -frame


def calculate_blastx_consistency(
    orf: ORFHit,
    hit: BlastXHit,
) -> BlastXConsistency:
    """Compare one selected ORF with an attached DIAMOND BLASTX hit."""

    blastx_coverage, orf_coverage = _interval_coverage(orf, hit)
    strand_agrees = orf.strand == hit.strand
    frame_agrees = _signed_frame(orf) == hit.query_frame

    amino_acid_identity: float | None = None
    subject_coverage: float | None = None
    length_agreement: float | None = None
    if hit.subject_protein:
        alignment = align_orf_proteins(
            orf.protein,
            hit.subject_protein,
            reference_id=hit.subject_id,
        )
        amino_acid_identity = alignment.amino_acid_identity
        subject_coverage = alignment.reference_coverage
        longest = max(orf.protein_length, len(hit.subject_protein))
        length_agreement = (
            min(orf.protein_length, len(hit.subject_protein)) / longest
            if longest
            else 0.0
        )

    warnings: list[str] = []
    if not strand_agrees:
        warnings.append("strand_disagreement")
    if not frame_agrees:
        warnings.append("frame_disagreement")
    if blastx_coverage < 0.90:
        warnings.append("selected_orf_does_not_cover_blastx_interval")
    if subject_coverage is not None and subject_coverage < 0.90:
        warnings.append("low_subject_protein_coverage")
    if amino_acid_identity is not None and amino_acid_identity < 0.70:
        warnings.append("low_subject_protein_identity")

    return BlastXConsistency(
        strand_agrees=strand_agrees,
        frame_agrees=frame_agrees,
        blastx_interval_coverage=blastx_coverage,
        orf_interval_coverage=orf_coverage,
        amino_acid_identity=amino_acid_identity,
        subject_coverage=subject_coverage,
        length_agreement=length_agreement,
        warnings=tuple(warnings),
    )


def attach_blastx_consistency(sample: Sample) -> None:
    """Attach BLASTX-versus-selected-ORF consistency metrics to candidates."""

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            hit = candidate.analysis.blastx
            metrics = candidate.analysis.orf
            selected = metrics.best_orf if metrics is not None else None
            if hit is None or selected is None:
                candidate.analysis.blastx_consistency = None
                continue
            candidate.analysis.blastx_consistency = calculate_blastx_consistency(
                selected,
                hit,
            )
