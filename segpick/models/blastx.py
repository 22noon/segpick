from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BlastXHit:
    """A DIAMOND BLASTX hit attached to a candidate contig."""

    query_id: str
    subject_id: str
    subject_title: str
    percent_identity: float
    alignment_length: int
    evalue: float
    bitscore: float
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    query_length: int
    subject_length: int
    query_frame: int
    subject_protein: str | None = field(default=None, repr=False)

    @property
    def strand(self) -> str:
        return "+" if self.query_frame > 0 else "-"

    @property
    def query_coverage(self) -> float:
        if self.query_length <= 0:
            return 0.0
        return (abs(self.query_end - self.query_start) + 1) / self.query_length

    @property
    def subject_coverage(self) -> float:
        if self.subject_length <= 0:
            return 0.0
        return (abs(self.subject_end - self.subject_start) + 1) / self.subject_length

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "subject_id": self.subject_id,
            "subject_title": self.subject_title,
            "percent_identity": self.percent_identity,
            "alignment_length": self.alignment_length,
            "evalue": self.evalue,
            "bitscore": self.bitscore,
            "query_start": self.query_start,
            "query_end": self.query_end,
            "subject_start": self.subject_start,
            "subject_end": self.subject_end,
            "query_length": self.query_length,
            "subject_length": self.subject_length,
            "query_frame": self.query_frame,
            "strand": self.strand,
            "query_coverage": self.query_coverage,
            "subject_coverage": self.subject_coverage,
            "subject_protein_found": self.subject_protein is not None,
        }
