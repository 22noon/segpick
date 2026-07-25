from __future__ import annotations

from dataclasses import dataclass

from .observation import ObservationInterval


@dataclass(frozen=True, slots=True)
class EvidenceConvergence:
    """Independent observations that converge on one protein region."""

    coordinate_system: str
    start: int
    end: int
    strength: str
    sources: tuple[str, ...]
    observation_types: tuple[str, ...]
    observations: tuple[ObservationInterval, ...]
    summary: str
    candidate_id: str

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError("start must be at least 1")
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        if len(set(self.sources)) < 2:
            raise ValueError("convergence requires at least two independent sources")

    @property
    def source_count(self) -> int:
        return len(set(self.sources))

    def to_dict(self) -> dict[str, object]:
        return {
            "coordinate_system": self.coordinate_system,
            "start": self.start,
            "end": self.end,
            "strength": self.strength,
            "sources": list(self.sources),
            "observation_types": list(self.observation_types),
            "observations": [item.to_dict() for item in self.observations],
            "summary": self.summary,
            "candidate_id": self.candidate_id,
            "source_count": self.source_count,
        }
