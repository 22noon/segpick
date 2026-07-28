from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReferenceCompatibility:
    """Compatibility of candidate organisation with the closest reference.

    This is an expectation-based channel. It intentionally excludes nucleotide
    identity and does not judge whether the candidate sequence is internally
    well assembled.
    """

    reference_id: str
    unsupported_internal_candidate_bases: int
    missing_internal_reference_bases: int
    duplicated_reference_bases: int
    internal_candidate_compatibility: float
    expected_reference_completeness: float
    block_order_compatibility: float
    orientation_compatibility: float
    duplication_compatibility: float
    score: float
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "reference_id": self.reference_id,
            "unsupported_internal_candidate_bases": self.unsupported_internal_candidate_bases,
            "missing_internal_reference_bases": self.missing_internal_reference_bases,
            "duplicated_reference_bases": self.duplicated_reference_bases,
            "internal_candidate_compatibility": self.internal_candidate_compatibility,
            "expected_reference_completeness": self.expected_reference_completeness,
            "block_order_compatibility": self.block_order_compatibility,
            "orientation_compatibility": self.orientation_compatibility,
            "duplication_compatibility": self.duplication_compatibility,
            "score": self.score,
            "status": self.status,
        }
