from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ObservationInterval:
    """A structural observation projected onto a shared coordinate system.

    Coordinates are 1-based and inclusive. Point observations use identical
    ``start`` and ``end`` coordinates.
    """

    coordinate_system: str
    start: int
    end: int
    observation_type: str
    source: str
    description: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError("start must be at least 1")
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "coordinate_system": self.coordinate_system,
            "start": self.start,
            "end": self.end,
            "observation_type": self.observation_type,
            "source": self.source,
            "description": self.description,
            "attributes": dict(self.attributes),
            "length": self.length,
        }
