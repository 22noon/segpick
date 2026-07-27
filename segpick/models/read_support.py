from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ReadSupportMetrics:
    """ORF-centred read-depth measurements for one candidate sequence.

    Region coordinates are zero-based and end-exclusive on the original contig.
    Whole-contig measurements are retained as contextual assembly information,
    while the primary evidence summaries describe the selected coding region.
    """

    sequence_id: str
    sequence_length: int
    region_source: str
    region_start: int
    region_end: int
    region_length: int
    mean_depth: float
    median_depth: float
    depth_sd: float
    any_covered_fraction: float
    covered_fraction: float
    uniformity: float
    left_terminal_support: float
    right_terminal_support: float
    longest_uncovered_interval: int
    longest_low_depth_interval: int
    internal_low_depth_interruption_count: int
    coverage_sufficiency: float
    coverage_integrity: float
    whole_contig_mean_depth: float
    whole_contig_median_depth: float
    whole_contig_covered_fraction: float

    @property
    def read_support(self) -> float:
        """Return the former combined summary for backwards compatibility."""

        return self.coverage_sufficiency * self.coverage_integrity

    def to_dict(self) -> dict[str, str | int | float]:
        """Return metrics as a plain dictionary."""

        payload = asdict(self)
        payload["read_support"] = self.read_support
        return payload
