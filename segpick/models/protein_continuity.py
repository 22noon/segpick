from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProteinContinuity:
    """Assembly-level interpretation of candidate protein-coordinate coverage."""

    classification: str
    candidate_count: int
    combined_coverage: float
    best_single_coverage: float
    complementary_candidate_ids: tuple[str, ...]
    redundant_overlap: bool
    uncovered_regions: tuple[tuple[float, float], ...]
    summary: str
    findings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "candidate_count": self.candidate_count,
            "combined_coverage": self.combined_coverage,
            "best_single_coverage": self.best_single_coverage,
            "complementary_candidate_ids": list(
                self.complementary_candidate_ids
            ),
            "redundant_overlap": self.redundant_overlap,
            "uncovered_regions": [list(region) for region in self.uncovered_regions],
            "summary": self.summary,
            "findings": list(self.findings),
        }
