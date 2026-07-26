from __future__ import annotations

from Bio.Seq import Seq

from segpick.models import BlastXAnchoredORF, BlastXHit, ORFHit, Sample

_STOP_CODONS = {"TAA", "TAG", "TGA"}
_START_CODON = "ATG"


def _normalise(sequence: str | Seq) -> str:
    return str(sequence).upper().replace("U", "T")


def _oriented_interval(hit: BlastXHit, sequence_length: int) -> tuple[int, int]:
    """Return zero-based, end-exclusive HSP coordinates on the coding strand."""

    original_start = min(hit.query_start, hit.query_end) - 1
    original_end = max(hit.query_start, hit.query_end)
    if hit.strand == "+":
        return original_start, original_end
    return sequence_length - original_end, sequence_length - original_start


def _original_coordinates(
    strand: str,
    sequence_length: int,
    oriented_start: int,
    oriented_end: int,
) -> tuple[int, int]:
    if strand == "+":
        return oriented_start, oriented_end
    return sequence_length - oriented_end, sequence_length - oriented_start


def _selected_comparison(
    anchored_start: int,
    anchored_end: int,
    strand: str,
    frame: int,
    selected: ORFHit | None,
) -> dict[str, object]:
    if selected is None:
        return {
            "selected_orf_available": False,
            "matches_selected_orf": False,
            "same_strand": None,
            "same_frame": None,
            "same_start": None,
            "same_end": None,
            "n_terminal_difference_aa": None,
            "c_terminal_difference_aa": None,
        }

    same_strand = selected.strand == strand
    same_frame = selected.frame == frame and same_strand
    same_start = selected.start == anchored_start
    same_end = selected.end == anchored_end

    if strand == "+":
        n_difference = (selected.start - anchored_start) // 3
        c_difference = (anchored_end - selected.end) // 3
    else:
        n_difference = (anchored_end - selected.end) // 3
        c_difference = (selected.start - anchored_start) // 3

    return {
        "selected_orf_available": True,
        "matches_selected_orf": (
            same_strand and same_frame and same_start and same_end
        ),
        "same_strand": same_strand,
        "same_frame": same_frame,
        "same_start": same_start,
        "same_end": same_end,
        "n_terminal_difference_aa": n_difference if same_strand else None,
        "c_terminal_difference_aa": c_difference if same_strand else None,
    }


def calculate_blastx_anchored_orf(
    sequence: str | Seq,
    hit: BlastXHit,
    selected_orf: ORFHit | None = None,
) -> BlastXAnchoredORF:
    """Extend a DIAMOND HSP to plausible in-frame coding boundaries.

    The extension remains on the DIAMOND strand and frame. Upstream, the first
    ATG after the previous in-frame stop is used when present. Downstream, the
    first in-frame stop after the HSP is used. Missing start/stop boundaries are
    retained as explicit partial states.
    """

    forward = _normalise(sequence)
    oriented = forward if hit.strand == "+" else str(Seq(forward).reverse_complement())
    frame = abs(hit.query_frame) - 1
    if frame not in {0, 1, 2}:
        raise ValueError(f"Unsupported DIAMOND query frame: {hit.query_frame}")

    hsp_start, hsp_end = _oriented_interval(hit, len(forward))
    usable_end = len(oriented) - ((len(oriented) - frame) % 3)

    # Codons that can contribute to the aligned interval.
    first_hsp_codon = frame + max(0, (hsp_start - frame) // 3) * 3
    last_hsp_codon = frame + max(0, (max(hsp_end - 1, frame) - frame) // 3) * 3

    previous_stop_end = frame
    starts: list[int] = []
    for position in range(frame, min(first_hsp_codon + 1, usable_end), 3):
        codon = oriented[position : position + 3]
        if codon in _STOP_CODONS:
            previous_stop_end = position + 3
            starts = []
        elif codon == _START_CODON and position >= previous_stop_end:
            starts.append(position)

    if starts:
        oriented_start = starts[0]
        has_start = True
    else:
        oriented_start = previous_stop_end
        has_start = False

    stop_end: int | None = None
    scan_start = max(frame, last_hsp_codon + 3)
    for position in range(scan_start, usable_end, 3):
        if oriented[position : position + 3] in _STOP_CODONS:
            stop_end = position + 3
            break

    if stop_end is None:
        oriented_end = usable_end
        has_stop = False
    else:
        oriented_end = stop_end
        has_stop = True

    coding_end = oriented_end - 3 if has_stop else oriented_end
    nucleotide_sequence = oriented[oriented_start:oriented_end]
    protein_sequence = str(Seq(oriented[oriented_start:coding_end]).translate())
    original_start, original_end = _original_coordinates(
        hit.strand,
        len(forward),
        oriented_start,
        oriented_end,
    )

    comparison = _selected_comparison(
        original_start,
        original_end,
        hit.strand,
        frame,
        selected_orf,
    )

    return BlastXAnchoredORF(
        start=original_start,
        end=original_end,
        strand=hit.strand,
        frame=frame,
        nucleotide_sequence=nucleotide_sequence,
        protein_sequence=protein_sequence,
        has_start_codon=has_start,
        has_stop_codon=has_stop,
        reaches_contig_start=original_start == 0,
        reaches_contig_end=original_end == len(forward),
        **comparison,
    )


def attach_blastx_anchored_orfs(sample: Sample) -> None:
    """Attach BLASTX-anchored coding sequences to candidates with DIAMOND hits."""

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            hit = candidate.analysis.blastx
            if hit is None:
                continue
            selected = (
                candidate.analysis.orf.best_orf
                if candidate.analysis.orf is not None
                else None
            )
            candidate.analysis.blastx_anchored_orf = calculate_blastx_anchored_orf(
                candidate.record.seq,
                hit,
                selected,
            )
