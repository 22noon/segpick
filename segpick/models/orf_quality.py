from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ORFQuality:
    """Explainable components describing candidate coding-sequence quality."""

    score: float
    complete_orf: float
    start_codon: float
    stop_codon: float
    protein_identity: float | None
    reference_coverage: float | None
    length_agreement: float | None
    terminal_completeness: float | None
    gap_integrity: float | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
