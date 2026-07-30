from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ObservationSource(StrEnum):
    """Independent source families used by evidence observations."""

    PROTEIN_ALIGNMENT = "protein_alignment"
    READ_COVERAGE = "read_coverage"
    ORF_STRUCTURE = "orf_structure"
    DIAMOND = "diamond"
    PROTEIN_CONTINUITY = "protein_continuity"
    STRUCTURAL_ALIGNMENT = "structural_alignment"
    REFERENCE_COMPATIBILITY = "reference_compatibility"
    CROSS_EVIDENCE = "cross_evidence"


@dataclass(frozen=True, slots=True)
class EvidenceObservation:
    """A factual observation, optionally located on a coordinate system.

    Spatial coordinates are 1-based and inclusive. Point observations use
    identical ``start`` and ``end`` values. Global observations leave
    ``coordinate_system``, ``start`` and ``end`` unset.
    """

    observation_type: str
    source: ObservationSource | str
    description: str
    coordinate_system: str | None = None
    start: int | None = None
    end: int | None = None
    severity: str = "informational"
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            source = ObservationSource(self.source)
        except ValueError:
            source = str(self.source).strip()
            if not source.startswith("plugin:"):
                raise ValueError(f"Unknown observation source: {self.source}")
        object.__setattr__(self, "source", source)

        coordinate_fields = (self.coordinate_system, self.start, self.end)
        supplied = tuple(value is not None for value in coordinate_fields)
        if any(supplied) and not all(supplied):
            raise ValueError(
                "coordinate_system, start and end must be supplied together"
            )
        if self.start is not None and self.start < 1:
            raise ValueError("start must be at least 1")
        if self.start is not None and self.end is not None and self.end < self.start:
            raise ValueError("end must be greater than or equal to start")

    @property
    def is_spatial(self) -> bool:
        return self.coordinate_system is not None

    @property
    def length(self) -> int | None:
        if self.start is None or self.end is None:
            return None
        return self.end - self.start + 1

    @property
    def source_name(self) -> str:
        return self.source.value if isinstance(self.source, ObservationSource) else str(self.source)

    def to_dict(self) -> dict[str, Any]:
        return {
            "coordinate_system": self.coordinate_system,
            "start": self.start,
            "end": self.end,
            "observation_type": self.observation_type,
            "source": self.source_name,
            "description": self.description,
            "severity": self.severity,
            "attributes": dict(self.attributes),
            "length": self.length,
            "is_spatial": self.is_spatial,
        }


# Backwards-compatible name retained for code that creates spatial observations.
ObservationInterval = EvidenceObservation
