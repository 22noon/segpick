from __future__ import annotations

from Bio.Seq import Seq

from segpick.analysis.orf import find_orfs, summarize_competing_orfs
from segpick.analysis.orf_alignment import align_orf_proteins
from segpick.models import BlastXHit, ORFHit, ORFMetrics, Sample


def _blastx_interval(hit: BlastXHit) -> tuple[int, int]:
    """Return the one-based inclusive BLASTX query interval as zero-based half-open."""

    return min(hit.query_start, hit.query_end) - 1, max(hit.query_start, hit.query_end)


def _interval_overlap_fraction(orf: ORFHit, hit: BlastXHit) -> float:
    blastx_start, blastx_end = _blastx_interval(hit)
    overlap = max(0, min(orf.end, blastx_end) - max(orf.start, blastx_start))
    blastx_length = blastx_end - blastx_start
    return overlap / blastx_length if blastx_length > 0 else 0.0


def _frame_agrees(orf: ORFHit, hit: BlastXHit) -> bool:
    expected_frame = orf.frame + 1
    if orf.strand == "-":
        expected_frame *= -1
    return expected_frame == hit.query_frame


def _same_orf(left: ORFHit | None, right: ORFHit | None) -> bool:
    if left is None or right is None:
        return left is right
    return (
        left.strand,
        left.frame,
        left.start,
        left.end,
    ) == (
        right.strand,
        right.frame,
        right.start,
        right.end,
    )


def calculate_blastx_guided_orf_metrics(
    sequence: str | Seq,
    hit: BlastXHit,
    *,
    minimum_protein_length: int = 20,
    include_partial: bool = True,
) -> ORFMetrics:
    """Select the ORF that best reconstructs the DIAMOND subject protein.

    Protein agreement is the primary criterion. Query-coordinate overlap,
    strand/frame agreement and ORF completeness are retained as tie-breakers,
    so DIAMOND guides selection without dictating it blindly.
    """

    hits = find_orfs(
        sequence,
        minimum_protein_length=minimum_protein_length,
        include_partial=include_partial,
    )
    longest = max(hits, key=lambda orf: orf.protein_length, default=None)

    if not hits or not hit.subject_protein:
        selected = hits[0] if hits else None
        other_complete, major_competing, largest_competing = summarize_competing_orfs(
            selected, hits
        )
        return ORFMetrics(
            best_orf=selected,
            orf_count=len(hits),
            complete_orf_count=sum(orf.complete for orf in hits),
            other_complete_orf_count=other_complete,
            major_competing_orf_count=major_competing,
            largest_competing_orf_length=largest_competing,
            longest_orf=longest,
            selection_method=(
                "longest_complete_orf"
                if selected and selected.complete
                else "longest_partial_orf"
                if selected
                else "no_orf"
            ),
            selected_matches_longest=_same_orf(selected, longest),
        )

    ranked: list[tuple[tuple[float, ...], ORFHit]] = []
    for orf in hits:
        alignment = align_orf_proteins(
            orf.protein,
            hit.subject_protein,
            reference_id=hit.subject_id,
        )
        protein_match = alignment.amino_acid_identity * alignment.reference_coverage
        rank = (
            protein_match,
            alignment.reference_coverage,
            alignment.amino_acid_identity,
            _interval_overlap_fraction(orf, hit),
            float(orf.strand == hit.strand),
            float(_frame_agrees(orf, hit)),
            float(orf.complete),
            float(orf.protein_length),
        )
        ranked.append((rank, orf))

    selected = max(ranked, key=lambda item: item[0])[1]
    other_complete, major_competing, largest_competing = summarize_competing_orfs(
        selected, hits
    )
    return ORFMetrics(
        best_orf=selected,
        orf_count=len(hits),
        complete_orf_count=sum(orf.complete for orf in hits),
        other_complete_orf_count=other_complete,
        major_competing_orf_count=major_competing,
        largest_competing_orf_length=largest_competing,
        longest_orf=longest,
        selection_method="blastx_protein_match",
        selected_matches_longest=_same_orf(selected, longest),
    )


def attach_blastx_guided_orf_metrics(
    sample: Sample,
    *,
    minimum_protein_length: int = 20,
    include_partial: bool = True,
) -> None:
    """Replace fallback ORF choices when resolved BLASTX proteins are available."""

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            hit = candidate.analysis.blastx
            if hit is None or hit.subject_protein is None:
                continue
            candidate.analysis.orf = calculate_blastx_guided_orf_metrics(
                candidate.record.seq,
                hit,
                minimum_protein_length=minimum_protein_length,
                include_partial=include_partial,
            )
