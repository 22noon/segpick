from __future__ import annotations

from Bio.Seq import Seq

from segpick.models import ORFHit, ORFMetrics, Sample

_STOP_CODONS = {"TAA", "TAG", "TGA"}
_START_CODON = "ATG"


def _normalise_sequence(sequence: str | Seq) -> str:
    return str(sequence).upper().replace("U", "T")


def _map_coordinates(
    strand: str,
    sequence_length: int,
    start: int,
    end: int,
) -> tuple[int, int]:
    if strand == "+":
        return start, end
    return sequence_length - end, sequence_length - start


def _make_orf(
    sequence: str,
    *,
    strand: str,
    frame: int,
    start: int,
    end: int,
    has_start_codon: bool,
    has_stop_codon: bool,
    original_length: int,
) -> ORFHit:
    coding_end = end - 3 if has_stop_codon else end
    protein = str(Seq(sequence[start:coding_end]).translate())
    original_start, original_end = _map_coordinates(
        strand,
        original_length,
        start,
        end,
    )
    return ORFHit(
        strand=strand,
        frame=frame,
        start=original_start,
        end=original_end,
        nucleotide_length=end - start,
        protein=protein,
        has_start_codon=has_start_codon,
        has_stop_codon=has_stop_codon,
    )


def _frame_orfs(
    sequence: str,
    *,
    strand: str,
    frame: int,
    original_length: int,
    include_partial: bool,
) -> list[ORFHit]:
    usable_end = len(sequence) - ((len(sequence) - frame) % 3)
    active_starts: list[int] = []
    region_start = frame
    hits: list[ORFHit] = []

    for position in range(frame, usable_end, 3):
        codon = sequence[position : position + 3]
        if codon == _START_CODON:
            active_starts.append(position)

        if codon not in _STOP_CODONS:
            continue

        stop_end = position + 3
        for start in active_starts:
            hits.append(
                _make_orf(
                    sequence,
                    strand=strand,
                    frame=frame,
                    start=start,
                    end=stop_end,
                    has_start_codon=True,
                    has_stop_codon=True,
                    original_length=original_length,
                )
            )

        if include_partial and not active_starts and stop_end > region_start:
            hits.append(
                _make_orf(
                    sequence,
                    strand=strand,
                    frame=frame,
                    start=region_start,
                    end=stop_end,
                    has_start_codon=False,
                    has_stop_codon=True,
                    original_length=original_length,
                )
            )

        active_starts = []
        region_start = stop_end

    if include_partial:
        for start in active_starts:
            if usable_end > start:
                hits.append(
                    _make_orf(
                        sequence,
                        strand=strand,
                        frame=frame,
                        start=start,
                        end=usable_end,
                        has_start_codon=True,
                        has_stop_codon=False,
                        original_length=original_length,
                    )
                )

        if not active_starts and usable_end > region_start:
            hits.append(
                _make_orf(
                    sequence,
                    strand=strand,
                    frame=frame,
                    start=region_start,
                    end=usable_end,
                    has_start_codon=False,
                    has_stop_codon=False,
                    original_length=original_length,
                )
            )

    return hits


def find_orfs(
    sequence: str | Seq,
    *,
    minimum_protein_length: int = 20,
    include_partial: bool = True,
) -> tuple[ORFHit, ...]:
    """Find ORFs in all six reading frames.

    Coordinates use Python convention: zero-based, end-exclusive positions on
    the original contig sequence. Reverse-strand hits are mapped back onto the
    original sequence coordinates.
    """

    if minimum_protein_length < 0:
        raise ValueError("minimum_protein_length must be non-negative")

    forward = _normalise_sequence(sequence)
    reverse = str(Seq(forward).reverse_complement())
    hits: list[ORFHit] = []

    for strand, strand_sequence in (("+", forward), ("-", reverse)):
        for frame in range(3):
            hits.extend(
                _frame_orfs(
                    strand_sequence,
                    strand=strand,
                    frame=frame,
                    original_length=len(forward),
                    include_partial=include_partial,
                )
            )

    filtered = [
        hit for hit in hits if hit.protein_length >= minimum_protein_length
    ]
    return tuple(
        sorted(
            filtered,
            key=lambda hit: (
                hit.complete,
                hit.protein_length,
                hit.has_start_codon,
            ),
            reverse=True,
        )
    )


def calculate_orf_metrics(
    sequence: str | Seq,
    *,
    minimum_protein_length: int = 20,
    include_partial: bool = True,
) -> ORFMetrics:
    hits = find_orfs(
        sequence,
        minimum_protein_length=minimum_protein_length,
        include_partial=include_partial,
    )
    selected = hits[0] if hits else None
    longest = max(hits, key=lambda hit: hit.protein_length, default=None)
    selection_method = (
        "longest_complete_orf"
        if selected and selected.complete
        else "longest_partial_orf"
        if selected
        else "no_orf"
    )
    return ORFMetrics(
        best_orf=selected,
        orf_count=len(hits),
        complete_orf_count=sum(hit.complete for hit in hits),
        longest_orf=longest,
        selection_method=selection_method,
        selected_matches_longest=(
            selected is None
            or longest is None
            or (
                selected.strand, selected.frame, selected.start, selected.end
            )
            == (
                longest.strand, longest.frame, longest.start, longest.end
            )
        ),
    )


def attach_orf_metrics(
    sample: Sample,
    *,
    minimum_protein_length: int = 20,
    include_partial: bool = True,
) -> None:
    """Attach six-frame ORF metrics to every candidate in a sample."""

    for gene in sample.genes.values():
        for candidate in gene.candidates:
            candidate.analysis.orf = calculate_orf_metrics(
                candidate.record.seq,
                minimum_protein_length=minimum_protein_length,
                include_partial=include_partial,
            )
