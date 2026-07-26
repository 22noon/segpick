from __future__ import annotations

from dataclasses import dataclass, field

from .blastx import BlastXHit
from .finding import BiologicalFinding
from .hypothesis import BiologicalHypothesis
from .blastx_consistency import BlastXConsistency
from .containment import ContainmentMetrics
from .convergence import EvidenceConvergence
from .orf import ORFMetrics
from .orf_alignment import ORFAlignmentMetrics
from .orf_quality import ORFQuality
from .observation import EvidenceObservation
from .protein_interpretation import ProteinInterpretation
from .protein_relatedness import ProteinRelatedness
from .read_support import ReadSupportMetrics
from .rule_evaluation import RuleEvaluation


@dataclass(slots=True)
class ContigAnalysis:
    """Derived analysis values for a candidate contig."""

    containment: ContainmentMetrics = field(
        default_factory=ContainmentMetrics
    )
    read_support: ReadSupportMetrics | None = None
    blastx: BlastXHit | None = None
    blastx_consistency: BlastXConsistency | None = None
    orf: ORFMetrics | None = None
    orf_alignment: ORFAlignmentMetrics | None = None
    orf_quality: ORFQuality | None = None
    protein_interpretation: ProteinInterpretation | None = None
    protein_relatedness: ProteinRelatedness | None = None
    observations: tuple[EvidenceObservation, ...] = ()
    convergences: tuple[EvidenceConvergence, ...] = ()
    findings: tuple[BiologicalFinding, ...] = ()
    hypotheses: tuple[BiologicalHypothesis, ...] = ()
    rule_evaluations: tuple[RuleEvaluation, ...] = ()
    depth_profile: dict[int, int] = field(default_factory=dict)
    recommendation_reason: str | None = None
