from dataclasses import dataclass


@dataclass(slots=True)
class Alignment:
    """One PAF alignment block between a query sequence and an anchor sequence."""

    query_id: str
    query_length: int
    query_start: int
    query_end: int
    strand: str
    target_id: str
    target_length: int
    target_start: int
    target_end: int
    matches: int
    alignment_length: int
    mapq: int

    @property
    def identity(self) -> float:
        return 0.0 if self.alignment_length == 0 else self.matches / self.alignment_length

    @property
    def query_coverage(self) -> float:
        return 0.0 if self.query_length == 0 else (self.query_end - self.query_start) / self.query_length

    @property
    def target_coverage(self) -> float:
        return 0.0 if self.target_length == 0 else (self.target_end - self.target_start) / self.target_length

    @property
    def query_span(self) -> int:
        return max(0, self.query_end - self.query_start)

    @property
    def target_span(self) -> int:
        return max(0, self.target_end - self.target_start)
