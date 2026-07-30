from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class BlastXConsistency:
    """Agreement between the selected ORF and its attached DIAMOND hit."""

    strand_agrees: bool
    frame_agrees: bool
    blastx_interval_coverage: float
    orf_interval_coverage: float
    amino_acid_identity: float | None
    subject_coverage: float | None
    length_agreement: float | None
    warnings: tuple[str, ...] = ()

    @property
    def coordinates_agree(self) -> bool:
        return self.blastx_interval_coverage >= 0.90

    @property
    def consistent(self) -> bool:
        return not self.warnings

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["coordinates_agree"] = self.coordinates_agree
        payload["consistent"] = self.consistent
        return payload
