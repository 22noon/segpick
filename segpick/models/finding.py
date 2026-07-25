from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class BiologicalFinding:
    """Structured biological interpretation supported by one or more sources."""

    category: str
    title: str
    severity: str
    confidence: str
    scope: str
    summary: str
    sources: tuple[str, ...]
    observation_types: tuple[str, ...] = ()
    candidate_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["sources"] = list(self.sources)
        data["observation_types"] = list(self.observation_types)
        data["candidate_ids"] = list(self.candidate_ids)
        return data
