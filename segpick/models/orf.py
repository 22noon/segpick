from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ORFHit:
    """A translated open reading frame found on one contig strand."""

    strand: str
    frame: int
    start: int
    end: int
    nucleotide_length: int
    protein: str
    has_start_codon: bool
    has_stop_codon: bool

    @property
    def protein_length(self) -> int:
        return len(self.protein)

    @property
    def complete(self) -> bool:
        return self.has_start_codon and self.has_stop_codon

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["protein_length"] = self.protein_length
        payload["complete"] = self.complete
        return payload


@dataclass(frozen=True, slots=True)
class ORFMetrics:
    """Summary of six-frame ORF discovery for one candidate contig."""

    best_orf: ORFHit | None
    orf_count: int
    complete_orf_count: int
    other_complete_orf_count: int = 0
    major_competing_orf_count: int = 0
    largest_competing_orf_length: int = 0
    longest_orf: ORFHit | None = None
    selection_method: str = "longest_complete_orf"
    selected_matches_longest: bool = True

    @property
    def longest_orf_nt(self) -> int:
        return self.best_orf.nucleotide_length if self.best_orf else 0

    @property
    def protein_length(self) -> int:
        return self.best_orf.protein_length if self.best_orf else 0

    @property
    def complete(self) -> bool:
        return self.best_orf.complete if self.best_orf else False

    def to_dict(self) -> dict[str, object]:
        return {
            "best_orf": self.best_orf.to_dict() if self.best_orf else None,
            "longest_orf": (
                self.longest_orf.to_dict() if self.longest_orf else None
            ),
            "selection_method": self.selection_method,
            "selected_matches_longest": self.selected_matches_longest,
            "orf_count": self.orf_count,
            "complete_orf_count": self.complete_orf_count,
            "other_complete_orf_count": self.other_complete_orf_count,
            "major_competing_orf_count": self.major_competing_orf_count,
            "largest_competing_orf_length": self.largest_competing_orf_length,
            "longest_orf_nt": self.longest_orf_nt,
            "protein_length": self.protein_length,
            "complete": self.complete,
        }
