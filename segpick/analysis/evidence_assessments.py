from __future__ import annotations

from collections.abc import Callable

from segpick.models import CandidateContig
from segpick.models.evidence_assessment import ConfidenceAssessment, ConfidenceFactor, EvidenceAssessment, EvidenceFinding
from segpick.scoring import CandidateRecommendation

AssessmentBuilder = Callable[[CandidateContig, CandidateRecommendation], EvidenceAssessment]
CHANNEL_REGISTRY: dict[str, AssessmentBuilder] = {}


def register_channel(channel_id: str):
    def decorator(function: AssessmentBuilder) -> AssessmentBuilder:
        if channel_id in CHANNEL_REGISTRY:
            raise ValueError(f"Evidence channel already registered: {channel_id}")
        CHANNEL_REGISTRY[channel_id] = function
        return function
    return decorator


def _level(value: float | None) -> str:
    if value is None:
        return "not_assessable"
    if value >= 0.80:
        return "strong"
    if value >= 0.60:
        return "moderate"
    if value >= 0.40:
        return "mixed"
    return "weak"


def _simple(channel_id: str, title: str, score: float | None, *, participates: bool, finding: str) -> EvidenceAssessment:
    available = score is not None
    confidence_score = 1.0 if available else None
    confidence = ConfidenceAssessment(
        level="high" if available else "not_assessable",
        score=confidence_score,
        method=f"{channel_id}_confidence",
        version="1.0",
        factors=(ConfidenceFactor("measurement_available", available, 1.0 if available else 0.0, "The channel score was successfully calculated."),),
        limitations=() if available else ("Required measurements were unavailable.",),
    )
    key = EvidenceFinding(f"{channel_id}_summary", finding if available else f"{title} could not be assessed", "Summary of the channel assessment.", "information", 10)
    return EvidenceAssessment(channel_id, title, "1.0", _level(score), score, confidence, key, measurements=(({"name": "score", "value": score},) if available else ()), limitations=confidence.limitations, participates_in_ranking=participates)


@register_channel("protein_confidence")
def protein(candidate, recommendation):
    return _simple("protein_confidence", "Protein evidence", recommendation.evidence.protein_confidence, participates=True, finding="Protein evidence supports the candidate")


@register_channel("read_evidence")
def reads(candidate, recommendation):
    values = [v for v in (recommendation.evidence.coverage_sufficiency, recommendation.evidence.coverage_integrity) if v is not None]
    score = sum(values) / len(values) if values else None
    result = _simple("read_evidence", "Read evidence", score, participates=True, finding="Read coverage supports the biologically relevant region")
    return result


@register_channel("structural_integrity")
def structural(candidate, recommendation):
    return _simple("structural_integrity", "Structural integrity", recommendation.evidence.structural_integrity, participates=True, finding="The candidate alignment is structurally coherent")


@register_channel("reference_compatibility")
def reference(candidate, recommendation):
    item = candidate.analysis.reference_compatibility
    if item is None:
        return _simple("reference_compatibility", "Reference compatibility", None, participates=False, finding="Reference compatibility could not be assessed")
    aligned_fraction = min(item.internal_candidate_compatibility, item.expected_reference_completeness)
    ambiguity = item.duplication_compatibility
    confidence_score = max(0.0, min(1.0, 0.75 * aligned_fraction + 0.25 * ambiguity))
    confidence = ConfidenceAssessment(
        level="high" if confidence_score >= .8 else "moderate" if confidence_score >= .6 else "low",
        score=confidence_score,
        method="reference_compatibility_confidence",
        version="1.0",
        factors=(
            ConfidenceFactor("aligned_fraction", aligned_fraction, 0.75 * aligned_fraction, "Coverage of both candidate and expected reference structure."),
            ConfidenceFactor("mapping_unambiguity", ambiguity, 0.25 * ambiguity, "Penalty for repeated mapping to the same reference region."),
        ),
        limitations=("Assessment depends on how representative the selected closest reference is.",),
    )
    findings = []
    if item.unsupported_internal_candidate_bases:
        findings.append(EvidenceFinding("unsupported_internal_candidate_region", f"Internal candidate region lacks reference support ({item.unsupported_internal_candidate_bases} nt)", "May indicate a genuine insertion, divergence, contamination, or misassembly.", "warning", 90))
    if item.missing_internal_reference_bases:
        findings.append(EvidenceFinding("missing_expected_reference_region", f"Expected internal reference region is missing ({item.missing_internal_reference_bases} nt)", "The candidate does not represent an internal region expected from the closest reference.", "warning", 85))
    if item.block_order_compatibility < 1:
        findings.append(EvidenceFinding("reference_block_order_disrupted", "Reference alignment blocks occur out of order", "May indicate rearrangement or assembly error.", "warning", 100))
    if item.orientation_compatibility < 1:
        findings.append(EvidenceFinding("unexpected_reference_orientation_switch", "Unexpected orientation change relative to reference", "May indicate inversion, chimera, or assembly error.", "warning", 95))
    if item.duplicated_reference_bases > 0:
        findings.append(EvidenceFinding("duplicated_reference_mapping", f"Separate candidate regions repeatedly map to the same reference interval ({item.duplicated_reference_bases} nt)", "May indicate duplication, repeat-associated ambiguity, or assembly error.", "warning", 88))
    if not findings:
        findings.append(EvidenceFinding("reference_organisation_compatible", "Reference organisation is compatible with the closest genome", "Expected block order, orientation, and internal continuity are preserved.", "information", 20))
    findings.sort(key=lambda value: value.priority, reverse=True)
    return EvidenceAssessment(
        "reference_compatibility", "Reference compatibility", "1.0", _level(item.score), item.score, confidence,
        findings[0], tuple(findings[1:]),
        measurements=(
            {"name": "unsupported_internal_candidate_bases", "value": item.unsupported_internal_candidate_bases},
            {"name": "missing_internal_reference_bases", "value": item.missing_internal_reference_bases},
            {"name": "block_order_compatibility", "value": item.block_order_compatibility},
            {"name": "orientation_compatibility", "value": item.orientation_compatibility},
            {"name": "duplicated_reference_bases", "value": item.duplicated_reference_bases},
            {"name": "duplication_compatibility", "value": item.duplication_compatibility},
        ),
        limitations=confidence.limitations,
        participates_in_ranking=False,
    )


@register_channel("length_plausibility")
def length(candidate, recommendation):
    return _simple("length_plausibility", "Length evidence", recommendation.evidence.length_plausibility, participates=True, finding="Candidate length is compatible with the expected segment length")


def build_evidence_assessments(candidate: CandidateContig, recommendation: CandidateRecommendation) -> tuple[EvidenceAssessment, ...]:
    return tuple(builder(candidate, recommendation) for builder in CHANNEL_REGISTRY.values())


def discover_external_channels(group: str = "segpick.evidence_channels") -> tuple[str, ...]:
    """Load installed evidence-channel entry points.

    Entry points must resolve to a callable accepting ``(candidate,
    recommendation)`` and returning ``EvidenceAssessment``. Discovery only
    registers assessment builders; it never grants ranking participation.
    """
    from importlib.metadata import entry_points

    loaded: list[str] = []
    selected = entry_points().select(group=group)
    for entry_point in selected:
        if entry_point.name in CHANNEL_REGISTRY:
            raise ValueError(f"Evidence channel already registered: {entry_point.name}")
        builder = entry_point.load()
        if not callable(builder):
            raise TypeError(f"Evidence channel {entry_point.name!r} is not callable")
        CHANNEL_REGISTRY[entry_point.name] = builder
        loaded.append(entry_point.name)
    return tuple(loaded)
