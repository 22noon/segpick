from __future__ import annotations

from dataclasses import dataclass


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

    @property
    def block_count(self) -> int:
        return len(self.hsps)

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
