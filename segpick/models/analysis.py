from dataclasses import dataclass, field

from .containment import ContainmentMetrics


@dataclass(slots=True)
class ContigAnalysis:
    containment: ContainmentMetrics = field(default_factory=ContainmentMetrics)
    recommendation_reason: str | None = None
