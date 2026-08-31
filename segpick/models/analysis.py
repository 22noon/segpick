from __future__ import annotations

from dataclasses import dataclass, field

from .blastx import BlastXHit
from .blastx_anchored_orf import BlastXAnchoredORF
from .blastx_consistency import BlastXConsistency
from .boundary_coverage import BoundaryCoverageAssessment
from .containment import ContainmentMetrics
from .convergence import EvidenceConvergence
from .cross_evidence import CrossEvidenceFinding
from .evidence_assessment import EvidenceAssessment
from .evidence_pattern import EvidencePatternEvaluation
from .finding import BiologicalFinding
from .hypothesis import BiologicalHypothesis
from .hypothesis_evaluation import HypothesisEvaluation
from .observation import EvidenceObservation
from .orf import ORFMetrics
from .orf_alignment import ORFAlignmentMetrics
from .orf_quality import ORFQuality
from .protein_interpretation import ProteinInterpretation
from .protein_relatedness import ProteinRelatedness
from .read_support import ReadSupportMetrics
from .reasoning_graph import MeasurementNode, ReasoningGraph
from .reference_compatibility import ReferenceCompatibility
from .reference_dotplot import ReferenceDotplot
from .rule_evaluation import RuleEvaluation
from .structural_integrity import StructuralIntegrity


@dataclass(slots=True)
class ContigAnalysis:
    """Derived analysis values for a candidate contig."""

    structural_integrity: StructuralIntegrity | None = None
    reference_compatibility: ReferenceCompatibility | None = None
    containment: ContainmentMetrics = field(default_factory=ContainmentMetrics)  # legacy data only
    read_support: ReadSupportMetrics | None = None
    reference_dotplot: ReferenceDotplot | None = None
    blastx: BlastXHit | None = None
    blastx_anchored_orf: BlastXAnchoredORF | None = None
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
    evidence_patterns: tuple[EvidencePatternEvaluation, ...] = ()
    unresolved_evidence_patterns: tuple[EvidencePatternEvaluation, ...] = ()
    biological_hypothesis_evaluations: tuple[HypothesisEvaluation, ...] = ()
    evidence_assessments: tuple[EvidenceAssessment, ...] = ()
    cross_evidence_findings: tuple[CrossEvidenceFinding, ...] = ()
    rule_evaluations: tuple[RuleEvaluation, ...] = ()
    depth_profile: dict[int, int] = field(default_factory=dict)
    boundary_coverage: tuple[BoundaryCoverageAssessment, ...] = ()
    recommendation_reason: str | None = None
    plugin_measurements: tuple[MeasurementNode, ...] = ()
    reasoning_graph: ReasoningGraph | None = None
    scientific_conclusions: tuple[ScientificConclusionEvaluation, ...] = ()

