from __future__ import annotations

from dataclasses import dataclass, field

from .containment import ContainmentMetrics
from .orf import ORFMetrics
from .orf_alignment import ORFAlignmentMetrics
from .orf_quality import ORFQuality
from .read_support import ReadSupportMetrics


@dataclass(slots=True)
class ContigAnalysis:
    """Derived analysis values for a candidate contig."""

    containment: ContainmentMetrics = field(
        default_factory=ContainmentMetrics
    )
    read_support: ReadSupportMetrics | None = None
    orf: ORFMetrics | None = None
    orf_alignment: ORFAlignmentMetrics | None = None
    orf_quality: ORFQuality | None = None
    recommendation_reason: str | None = None
