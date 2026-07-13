from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ReadSupportMetrics:
    """Read-depth support metrics for one candidate sequence."""

    sequence_id: str
    sequence_length: int
    mean_depth: float
    median_depth: float
    depth_sd: float
    covered_fraction: float
    uniformity: float
    left_terminal_support: float
    right_terminal_support: float
    read_support: float

    def to_dict(self) -> dict[str, str | int | float]:
        """Return metrics as a plain dictionary."""

        return asdict(self)
