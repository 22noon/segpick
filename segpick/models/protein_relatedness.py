from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProteinRelatedness:
    """Contextual interpretation of DIAMOND protein-homology evidence."""

    subject_id: str
    subject_title: str
    percent_identity: float
    query_coverage: float
    subject_coverage: float
    bitscore: float
    evalue: float
    expected_gene_agrees: bool | None
    top_hit_count: int
    top_hit_gene_agreement: float | None
    classification: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_title": self.subject_title,
            "percent_identity": self.percent_identity,
            "query_coverage": self.query_coverage,
            "subject_coverage": self.subject_coverage,
            "bitscore": self.bitscore,
            "evalue": self.evalue,
            "expected_gene_agrees": self.expected_gene_agrees,
            "top_hit_count": self.top_hit_count,
            "top_hit_gene_agreement": self.top_hit_gene_agreement,
            "classification": self.classification,
            "summary": self.summary,
        }
