from __future__ import annotations

from dataclasses import dataclass


def _interval_overlap(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int] | None:
    left = max(min(a), min(b))
    right = min(max(a), max(b))
    return (left, right) if right >= left else None


@dataclass(frozen=True, slots=True)
class BlastNHSP:
    query_id: str
    subject_id: str
    query_length: int
    subject_length: int
    percent_identity: float
    alignment_length: int
    mismatches: int
    gap_opens: int
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    evalue: float
    bitscore: float

    @property
    def strand(self) -> str:
        return "+" if self.subject_end >= self.subject_start else "-"


    def to_dict(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "subject_id": self.subject_id,
            "query_length": self.query_length,
            "subject_length": self.subject_length,
            "percent_identity": self.percent_identity,
            "alignment_length": self.alignment_length,
            "mismatches": self.mismatches,
            "gap_opens": self.gap_opens,
            "query_start": self.query_start,
            "query_end": self.query_end,
            "subject_start": self.subject_start,
            "subject_end": self.subject_end,
            "strand": self.strand,
            "evalue": self.evalue,
            "bitscore": self.bitscore,
        }


@dataclass(frozen=True, slots=True)
class ReferenceDotplot:
    candidate_id: str
    reference_id: str
    query_length: int
    reference_length: int
    hsps: tuple[BlastNHSP, ...]
    query_coverage: float
    reference_coverage: float
    identity_min: float | None
    identity_max: float | None
    output_path: str
    reused_existing: bool

    @property
    def available(self) -> bool:
        return bool(self.hsps)

    def merged_query_intervals(self, *, maximum_gap: int = 25) -> tuple[tuple[int, int], ...]:
        """Return merged one-based inclusive query intervals for all HSPs."""

        intervals = sorted(
            (min(hsp.query_start, hsp.query_end), max(hsp.query_start, hsp.query_end))
            for hsp in self.hsps
        )
        merged: list[list[int]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1] + maximum_gap + 1:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        return tuple((start, end) for start, end in merged)

    @property
    def block_count(self) -> int:
        return len(self.hsps)

    def repeated_reference_pairs(self) -> tuple[dict[str, object], ...]:
        """Return distinct query-block pairs that overlap on the reference.

        A pair is diagnostic only when its query intervals do not overlap but
        its reference intervals do. This is the same structural pattern used
        by the reference-compatibility duplication assessment.
        """

        pairs: list[dict[str, object]] = []
        for left_index, left in enumerate(self.hsps):
            for right_index in range(left_index + 1, len(self.hsps)):
                right = self.hsps[right_index]
                query_overlap = _interval_overlap(
                    (left.query_start, left.query_end),
                    (right.query_start, right.query_end),
                )
                if query_overlap is not None:
                    continue
                reference_overlap = _interval_overlap(
                    (left.subject_start, left.subject_end),
                    (right.subject_start, right.subject_end),
                )
                if reference_overlap is None:
                    continue
                pairs.append(
                    {
                        "left_hsp_index": left_index,
                        "right_hsp_index": right_index,
                        "left_query_interval": (min(left.query_start, left.query_end), max(left.query_start, left.query_end)),
                        "right_query_interval": (min(right.query_start, right.query_end), max(right.query_start, right.query_end)),
                        "reference_interval": reference_overlap,
                        "overlap_bases": reference_overlap[1] - reference_overlap[0] + 1,
                    }
                )
        return tuple(pairs)

    @property
    def repeated_reference_hsp_indices(self) -> tuple[int, ...]:
        indices = {
            int(pair[key])
            for pair in self.repeated_reference_pairs()
            for key in ("left_hsp_index", "right_hsp_index")
        }
        return tuple(sorted(indices))


    def architecture_blocks(self, *, maximum_gap: int = 25) -> tuple[dict[str, object], ...]:
        """Return query-ordered HSP blocks for contig-centric interpretation."""

        repeated = set(self.repeated_reference_hsp_indices)
        ordered = sorted(
            enumerate(self.hsps),
            key=lambda item: (
                min(item[1].query_start, item[1].query_end),
                max(item[1].query_start, item[1].query_end),
            ),
        )
        blocks: list[dict[str, object]] = []
        previous_end: int | None = None
        for order, (hsp_index, hsp) in enumerate(ordered, start=1):
            query_start = min(hsp.query_start, hsp.query_end)
            query_end = max(hsp.query_start, hsp.query_end)
            reference_start = min(hsp.subject_start, hsp.subject_end)
            reference_end = max(hsp.subject_start, hsp.subject_end)
            gap_before = (query_start - previous_end - 1) if previous_end is not None else query_start - 1
            blocks.append(
                {
                    "order": order,
                    "hsp_index": hsp_index,
                    "query_interval": (query_start, query_end),
                    "reference_interval": (reference_start, reference_end),
                    "query_bases": query_end - query_start + 1,
                    "reference_bases": reference_end - reference_start + 1,
                    "strand": hsp.strand,
                    "gap_before": max(0, gap_before),
                    "substantial_gap_before": gap_before > maximum_gap,
                    "repeated_reference_mapping": hsp_index in repeated,
                    "percent_identity": hsp.percent_identity,
                    "bitscore": hsp.bitscore,
                }
            )
            previous_end = max(previous_end or 0, query_end)
        return tuple(blocks)

    def architecture_summary(self, *, maximum_gap: int = 25) -> dict[str, object]:
        """Summarise directly observable candidate alignment architecture."""

        blocks = self.architecture_blocks(maximum_gap=maximum_gap)
        if not blocks:
            return {
                "primary_classification": "No reference alignment",
                "classifications": ("no_reference_alignment",),
                "block_count": 0,
                "substantial_internal_gap_count": 0,
                "mixed_orientation": False,
                "reference_order_consistent": None,
                "repeated_reference_mapping": False,
                "terminal_left_unaligned_bases": self.query_length,
                "terminal_right_unaligned_bases": self.query_length,
            }

        strands = {str(block["strand"]) for block in blocks}
        mixed_orientation = len(strands) > 1
        substantial_gaps = sum(bool(block["substantial_gap_before"]) for block in blocks[1:])
        repeated = bool(self.repeated_reference_pairs())
        first_query = int(blocks[0]["query_interval"][0])
        last_query = max(int(block["query_interval"][1]) for block in blocks)

        reference_order_consistent: bool | None = None
        if not mixed_orientation and len(blocks) > 1:
            midpoints = [
                (int(block["reference_interval"][0]) + int(block["reference_interval"][1])) / 2
                for block in blocks
            ]
            if next(iter(strands)) == "+":
                reference_order_consistent = all(a <= b for a, b in zip(midpoints, midpoints[1:]))
            else:
                reference_order_consistent = all(a >= b for a, b in zip(midpoints, midpoints[1:]))

        classifications: list[str] = []
        if repeated:
            classifications.append("repeated_reference_mapping")
        if mixed_orientation:
            classifications.append("mixed_orientation")
        if reference_order_consistent is False:
            classifications.append("reordered_reference_progression")
        if substantial_gaps:
            classifications.append("fragmented_alignment")
        if len(blocks) == 1:
            classifications.append("single_alignment_block")
        elif not classifications:
            classifications.append("collinear_alignment")

        if repeated:
            primary = "Repeated-reference architecture"
        elif mixed_orientation:
            primary = "Mixed-orientation architecture"
        elif reference_order_consistent is False:
            primary = "Reordered reference progression"
        elif substantial_gaps:
            primary = "Fragmented collinear architecture"
        elif len(blocks) == 1:
            primary = "Single alignment block"
        else:
            primary = "Collinear architecture"

        return {
            "primary_classification": primary,
            "classifications": tuple(classifications),
            "block_count": len(blocks),
            "substantial_internal_gap_count": substantial_gaps,
            "mixed_orientation": mixed_orientation,
            "reference_order_consistent": reference_order_consistent,
            "repeated_reference_mapping": repeated,
            "terminal_left_unaligned_bases": max(0, first_query - 1),
            "terminal_right_unaligned_bases": max(0, self.query_length - last_query),
        }

    @property
    def orientation(self) -> str:
        strands = {hsp.strand for hsp in self.hsps}
        if not strands:
            return "unavailable"
        if strands == {"+"}:
            return "forward"
        if strands == {"-"}:
            return "reverse"
        return "mixed"

    @property
    def forward_support(self) -> int:
        return sum(hsp.alignment_length for hsp in self.hsps if hsp.strand == "+")

    @property
    def reverse_support(self) -> int:
        return sum(hsp.alignment_length for hsp in self.hsps if hsp.strand == "-")

    @property
    def dominant_orientation_fraction(self) -> float | None:
        total = self.forward_support + self.reverse_support
        if total == 0:
            return None
        return max(self.forward_support, self.reverse_support) / total

    @property
    def display_orientation(self) -> str:
        fraction = self.dominant_orientation_fraction
        if fraction is None or fraction < 0.80:
            return "uncertain" if self.hsps else "unavailable"
        return "reverse" if self.reverse_support > self.forward_support else "forward"

    @property
    def display_reverse_complemented(self) -> bool:
        return self.display_orientation == "reverse"

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "reference_id": self.reference_id,
            "query_length": self.query_length,
            "reference_length": self.reference_length,
            "hsps": [hsp.to_dict() for hsp in self.hsps],
            "query_coverage": self.query_coverage,
            "reference_coverage": self.reference_coverage,
            "identity_min": self.identity_min,
            "identity_max": self.identity_max,
            "block_count": self.block_count,
            "repeated_reference_pairs": list(self.repeated_reference_pairs()),
            "repeated_reference_hsp_indices": list(self.repeated_reference_hsp_indices),
            "architecture_blocks": list(self.architecture_blocks()),
            "architecture_summary": self.architecture_summary(),
            "orientation": self.orientation,
            "forward_support": self.forward_support,
            "reverse_support": self.reverse_support,
            "dominant_orientation_fraction": self.dominant_orientation_fraction,
            "display_orientation": self.display_orientation,
            "display_reverse_complemented": self.display_reverse_complemented,
            "output_path": self.output_path,
            "reused_existing": self.reused_existing,
            "available": self.available,
        }
