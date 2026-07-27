from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StructuralIntegrity:
    """Reference-relative nucleotide structural measurements from BLAST HSPs."""

    reference_id: str
    candidate_coverage: float
    reference_coverage: float
    block_count: int
    longest_block_fraction: float
    largest_candidate_gap: int
    largest_reference_gap: int
    continuity: float
    orientation_consistency: float
    order_consistency: float
    score: float
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "reference_id": self.reference_id,
            "candidate_coverage": self.candidate_coverage,
            "reference_coverage": self.reference_coverage,
            "block_count": self.block_count,
            "longest_block_fraction": self.longest_block_fraction,
            "largest_candidate_gap": self.largest_candidate_gap,
            "largest_reference_gap": self.largest_reference_gap,
            "continuity": self.continuity,
            "orientation_consistency": self.orientation_consistency,
            "order_consistency": self.order_consistency,
            "score": self.score,
            "status": self.status,
        }
