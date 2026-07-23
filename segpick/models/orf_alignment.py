from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ORFAlignmentMetrics:
    """Protein-alignment measurements for a candidate ORF and its reference."""

    reference_id: str
    candidate_protein_length: int
    reference_protein_length: int
    aligned_residues: int
    identical_residues: int
    amino_acid_identity: float
    candidate_coverage: float
    reference_coverage: float
    length_ratio: float
    n_terminal_missing: int
    c_terminal_missing: int
    internal_gap_residues: int

    def to_dict(self) -> dict[str, str | int | float]:
        return asdict(self)
