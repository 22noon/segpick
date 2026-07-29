from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class BoundaryCoverageAssessment:
    """Read-depth behaviour across one internal reference-alignment gap.

    The gap is candidate sequence absent from the selected reference.  Regional
    measurements ask whether that sequence is represented by reads, while the
    left and right junction measurements ask whether depth changes smoothly at
    each attachment point.  Depth continuity is not equivalent to direct
    split-read or read-spanning evidence and is deliberately labelled as such.
    """

    candidate_id: str
    reference_id: str
    gap_start: int
    gap_end: int
    gap_length: int
    flank_window: int
    left_median_depth: float
    gap_median_depth: float
    right_median_depth: float
    baseline_depth: float
    gap_to_baseline_ratio: float | None
    zero_fraction: float
    classification: str
    severity: str
    summary: str
    junction_window: int = 10
    left_inner_median_depth: float = 0.0
    right_inner_median_depth: float = 0.0
    left_junction_ratio: float | None = None
    right_junction_ratio: float | None = None
    left_junction_smooth: bool | None = None
    right_junction_smooth: bool | None = None
    regional_sequence_supported: bool | None = None
    placement_interpretation: str = "not_assessable"

    @property
    def both_junctions_smooth(self) -> bool | None:
        if self.left_junction_smooth is None or self.right_junction_smooth is None:
            return None
        return self.left_junction_smooth and self.right_junction_smooth

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["both_junctions_smooth"] = self.both_junctions_smooth
        return payload
