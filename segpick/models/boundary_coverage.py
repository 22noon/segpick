from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class BoundaryCoverageAssessment:
    """Coverage behaviour across one internal reference-alignment gap."""

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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
