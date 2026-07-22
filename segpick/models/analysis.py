from __future__ import annotations

from dataclasses import dataclass, field

from .containment import ContainmentMetrics
from .orf import ORFMetrics
from .read_support import ReadSupportMetrics


@dataclass(slots=True)
class ContigAnalysis:
    """Derived analysis values for a candidate contig."""

    containment: ContainmentMetrics = field(
        default_factory=ContainmentMetrics
    )
    read_support: ReadSupportMetrics | None = None
    orf: ORFMetrics | None = None
    recommendation_reason: str | None = None
