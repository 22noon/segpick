from __future__ import annotations

from collections.abc import Callable

from segpick.models import CandidateContig
from segpick.models.evidence_assessment import AssessmentDiagnostics, ConfidenceAssessment, ConfidenceFactor, DiagnosticCheck, EvidenceAssessment, EvidenceFinding
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
    if score is None:
        return _simple(
            "read_evidence", "Read evidence", None,
            participates=True,
            finding="Read coverage could not be assessed",
        )

    supported = score >= 0.60
    finding = EvidenceFinding(
        "read_region_supported" if supported else "read_region_limited_support",
        "Read coverage supports the biologically relevant region" if supported else "Read coverage provides limited support for the biologically relevant region",
        "Regional read-depth evidence summarises whether the selected coding region is represented consistently.",
        "information" if supported else "warning",
        50,
    )
    confidence = ConfidenceAssessment(
        level="high",
        score=1.0,
        method="read_evidence_measurement_confidence",
        version="1.0",
        factors=(ConfidenceFactor("measurement_available", True, 1.0, "Read-depth measurements were successfully calculated."),),
        limitations=("Regional support does not establish that reads span a specific structural junction.",),
    )
    return EvidenceAssessment(
        "read_evidence", "Read evidence", "1.1", _level(score), score,
        confidence, finding,
        measurements=({"name": "score", "value": score},),
        limitations=confidence.limitations,
        participates_in_ranking=True,
    )


@register_channel("junction_read_support")
def junction_reads(candidate, recommendation):
    """Summarise depth continuity across reference-absent interval junctions.

    This explanatory channel is independent of the regional read-evidence
    score and never participates in ranking.  It uses local depth smoothness,
    not direct evidence that individual reads span a junction.
    """

    boundaries = tuple(candidate.analysis.boundary_coverage)
    dotplot = candidate.analysis.reference_dotplot
    profile = candidate.analysis.depth_profile
    compatibility = candidate.analysis.reference_compatibility

    dotplot_available = dotplot is not None
    hsps_available = bool(dotplot and dotplot.hsps)
    depth_available = bool(profile)
    unsupported_bases = (
        compatibility.unsupported_internal_candidate_bases
        if compatibility is not None
        else None
    )
    unsupported_reported = unsupported_bases is not None and unsupported_bases > 0

    diagnostic_checks = [
        DiagnosticCheck(
            "reference_dotplot_available",
            "Reference dot plot available",
            "pass" if dotplot_available else "fail",
            "Candidate-to-reference alignment data are required to locate internal reference-absent intervals.",
            dotplot_available,
        ),
        DiagnosticCheck(
            "reference_hsps_available",
            "Reference alignment blocks available",
            "pass" if hsps_available else ("fail" if dotplot_available else "not_run"),
            "At least two usable alignment blocks are generally needed to define an internal candidate interval.",
            len(dotplot.hsps) if dotplot is not None else 0,
        ),
        DiagnosticCheck(
            "depth_profile_available",
            "Per-base depth profile available",
            "pass" if depth_available else "fail",
            "Junction smoothness requires the candidate's per-base depth profile.",
            len(profile),
        ),
        DiagnosticCheck(
            "reference_absent_sequence_reported",
            "Reference compatibility reports internal unsupported sequence",
            "pass" if unsupported_reported else ("warn" if compatibility is not None else "not_run"),
            "This summarises whether Reference Compatibility detected internal candidate sequence absent from the closest reference.",
            unsupported_bases,
        ),
        DiagnosticCheck(
            "boundary_intervals_constructed",
            "Assessable junction intervals constructed",
            "pass" if boundaries else "fail",
            "Intervals must occur between distinct merged reference-alignment blocks and retain usable flanking and interval depth windows.",
            len(boundaries),
        ),
    ]

    if not boundaries:
        if not dotplot_available:
            reason = "No candidate-to-reference dot plot was attached."
        elif not hsps_available:
            reason = "The reference dot plot contained no usable alignment blocks."
        elif not depth_available:
            reason = "No per-base depth profile was attached to this candidate."
        elif dotplot and len(dotplot.merged_query_intervals(maximum_gap=25)) < 2:
            reason = (
                "No internal interval remained between merged reference-alignment blocks. "
                "The Reference Compatibility summary may count unsupported sequence that is terminal, contained within a merged block gap, or not represented by explicit interval coordinates."
            )
        else:
            reason = (
                "Candidate intervals were identified, but none retained usable depth windows on the interval and both flanks. "
                "This can occur near contig ends or when interval coordinates fall outside the loaded depth profile."
            )
        diagnostics = AssessmentDiagnostics(tuple(diagnostic_checks), reason)
        confidence = ConfidenceAssessment(
            level="not_assessable",
            score=None,
            method="junction_read_support_confidence",
            version="1.1",
            factors=(
                ConfidenceFactor(
                    "measurement_available",
                    False,
                    0.0,
                    reason,
                ),
            ),
            limitations=(reason,),
        )
        return EvidenceAssessment(
            "junction_read_support",
            "Junction read support",
            "1.1",
            "not_assessable",
            None,
            confidence,
            EvidenceFinding(
                "junction_read_support_not_assessable",
                "Junction read support could not be assessed",
                reason,
                "information",
                10,
            ),
            measurements=(
                {"name": "reference_dotplot_available", "value": dotplot_available},
                {"name": "reference_hsp_count", "value": len(dotplot.hsps) if dotplot else 0},
                {"name": "depth_positions_available", "value": len(profile)},
                {"name": "unsupported_internal_candidate_bases", "value": unsupported_bases},
                {"name": "boundary_interval_count", "value": 0},
            ),
            limitations=(reason,),
            participates_in_ranking=False,
            diagnostics=diagnostics,
        )

    findings: list[EvidenceFinding] = []
    scores: list[float] = []
    measurements: list[dict[str, object]] = []
    assessable_junctions = 0

    for index, item in enumerate(boundaries, start=1):
        left = item.left_junction_ratio
        right = item.right_junction_ratio
        available = [value for value in (left, right) if value is not None]
        if available:
            scores.append(sum(available) / len(available))
            assessable_junctions += len(available)

        interval = f"{item.gap_start}-{item.gap_end}"
        measurements.extend((
            {"name": f"boundary_{index}_interval", "value": interval},
            {"name": f"boundary_{index}_regional_supported", "value": item.regional_sequence_supported},
            {"name": f"boundary_{index}_left_junction_ratio", "value": left},
            {"name": f"boundary_{index}_right_junction_ratio", "value": right},
            {"name": f"boundary_{index}_placement_interpretation", "value": item.placement_interpretation},
        ))

        if item.classification in {"continuous_coverage", "supported_with_smooth_junctions"}:
            findings.append(EvidenceFinding(
                "reference_absent_interval_smooth_both_junctions",
                f"Reference-absent interval has smooth depth across both junctions ({interval})",
                "Regional coverage and local depth continuity support the assembled placement, although depth alone does not prove read spanning.",
                "information", 85,
            ))
        elif item.classification == "supported_with_junction_discontinuity":
            findings.append(EvidenceFinding(
                "reference_absent_sequence_supported_junction_discontinuous",
                f"Reference-absent sequence is covered but junction depth is discontinuous ({interval})",
                "The sequence itself may be genuine, while an abrupt depth transition raises uncertainty about its assembled position.",
                "warning", 100,
            ))
            if item.left_junction_smooth is False:
                findings.append(EvidenceFinding(
                    "left_reference_absent_junction_discontinuous",
                    f"Left junction has an abrupt depth transition ({interval})",
                    "The left attachment of the reference-absent interval requires review.",
                    "warning", 95,
                ))
            if item.right_junction_smooth is False:
                findings.append(EvidenceFinding(
                    "right_reference_absent_junction_discontinuous",
                    f"Right junction has an abrupt depth transition ({interval})",
                    "The right attachment of the reference-absent interval requires review.",
                    "warning", 95,
                ))
        elif item.regional_sequence_supported is False:
            findings.append(EvidenceFinding(
                "reference_absent_interval_weak_regional_support",
                f"Reference-absent interval has weak regional read support ({interval})",
                "The candidate interval may be unsupported sequence or may lie in a locally under-sampled region.",
                "warning", 90,
            ))
        else:
            findings.append(EvidenceFinding(
                "reference_absent_junctions_not_assessable",
                f"Junction smoothness is not assessable ({interval})",
                "Regional coverage may be present, but local junction depth is insufficient for placement interpretation.",
                "information", 40,
            ))

    findings.sort(key=lambda value: value.priority, reverse=True)
    score = sum(scores) / len(scores) if scores else None
    completeness = assessable_junctions / max(2 * len(boundaries), 1)
    confidence_score = min(1.0, completeness * (0.5 + 0.5 * min(1.0, len(boundaries))))
    confidence = ConfidenceAssessment(
        level="high" if confidence_score >= .8 else "moderate" if confidence_score >= .6 else "low",
        score=confidence_score,
        method="junction_depth_continuity_confidence",
        version="1.0",
        factors=(
            ConfidenceFactor(
                "assessable_junction_fraction",
                completeness,
                confidence_score,
                "Fraction of left and right junctions with sufficient local depth for comparison.",
            ),
        ),
        limitations=(
            "Depth smoothness does not prove that individual reads or read pairs span either junction.",
            "Mapping ambiguity and repeats can produce apparently smooth depth across an incorrect join.",
        ),
    )
    return EvidenceAssessment(
        "junction_read_support",
        "Junction read support",
        "1.0",
        _level(score),
        score,
        confidence,
        findings[0],
        tuple(findings[1:]),
        measurements=tuple(measurements),
        limitations=confidence.limitations,
        participates_in_ranking=False,
        diagnostics=AssessmentDiagnostics(tuple(diagnostic_checks), None),
    )


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
