from __future__ import annotations

from dataclasses import dataclass

from segpick.analysis import analyse_protein_continuity
from segpick.models import BiologicalHypothesis, BiologicalScenario, CandidateContig, Gene, RuleEvaluation
from segpick.scoring import GeneRecommendation
from segpick.knowledge.vocabulary import ConditionDisplay, describe_condition






@dataclass(frozen=True, slots=True)
class ScenarioView:
    scenario_id: str
    title: str
    category: str
    scope: str
    confidence: str
    severity: str
    interpretation: str
    candidate_ids: tuple[str, ...]
    matched_required: tuple[ConditionDisplay, ...]
    matched_supporting: tuple[ConditionDisplay, ...]
    matched_conflicting: tuple[ConditionDisplay, ...]
    suggested_actions: tuple[str, ...]
    source: str
    references: tuple[str, ...]

def build_scenario_view(item: BiologicalScenario) -> ScenarioView:
    return ScenarioView(
        scenario_id=item.scenario_id,
        title=item.title,
        category=item.category,
        scope=item.scope,
        confidence=item.confidence,
        severity=item.severity,
        interpretation=item.interpretation,
        candidate_ids=item.candidate_ids,
        matched_required=tuple(describe_condition(value) for value in item.matched_required),
        matched_supporting=tuple(describe_condition(value) for value in item.matched_supporting),
        matched_conflicting=tuple(describe_condition(value) for value in item.matched_conflicting),
        suggested_actions=item.suggested_actions,
        source=item.source,
        references=item.references,
    )

@dataclass(frozen=True, slots=True)
class RuleEvaluationView:
    rule_id: str
    title: str
    scope: str
    triggered: bool
    confidence: str | None
    severity: str
    rule_source: str
    rule_description: str
    rule_references: tuple[str, ...]
    matched_required: tuple[str, ...]
    missing_required: tuple[str, ...]
    matched_supporting: tuple[str, ...]
    missing_supporting: tuple[str, ...]
    matched_conflicting: tuple[str, ...]

def build_rule_evaluation_view(item: RuleEvaluation) -> RuleEvaluationView:
    return RuleEvaluationView(**{name: getattr(item, name) for name in RuleEvaluationView.__dataclass_fields__})

@dataclass(frozen=True, slots=True)
class HypothesisView:
    rule_id: str
    title: str
    category: str
    scope: str
    confidence: str
    severity: str
    summary: str
    candidate_ids: tuple[str, ...]
    matched_required: tuple[str, ...]
    matched_supporting: tuple[str, ...]
    matched_conflicting: tuple[str, ...]
    rule_source: str
    rule_description: str
    rule_references: tuple[str, ...]


def build_hypothesis_view(hypothesis: BiologicalHypothesis) -> HypothesisView:
    return HypothesisView(
        rule_id=hypothesis.rule_id,
        title=hypothesis.title,
        category=hypothesis.category,
        scope=hypothesis.scope,
        confidence=hypothesis.confidence,
        severity=hypothesis.severity,
        summary=hypothesis.summary,
        candidate_ids=hypothesis.candidate_ids,
        matched_required=hypothesis.matched_required,
        matched_supporting=hypothesis.matched_supporting,
        matched_conflicting=hypothesis.matched_conflicting,
        rule_source=hypothesis.rule_source,
        rule_description=hypothesis.rule_description,
        rule_references=hypothesis.rule_references,
    )


@dataclass(frozen=True, slots=True)
class ReadSupportView:
    available: bool
    region_source: str | None
    region_start: int | None
    region_end: int | None
    region_length: int | None
    mean_depth: float | None
    median_depth: float | None
    any_covered_fraction: float | None
    covered_fraction: float | None
    uniformity: float | None
    left_terminal_support: float | None
    right_terminal_support: float | None
    longest_uncovered_interval: int | None
    longest_low_depth_interval: int | None
    internal_low_depth_interruption_count: int | None
    coverage_sufficiency: float | None
    coverage_integrity: float | None
    whole_contig_covered_fraction: float | None

    @property
    def overall_support(self) -> float | None:
        if self.coverage_sufficiency is None or self.coverage_integrity is None:
            return None
        return self.coverage_sufficiency * self.coverage_integrity


@dataclass(frozen=True, slots=True)
class ProteinRelatednessView:
    available: bool
    subject_id: str | None
    subject_title: str | None
    percent_identity: float | None
    query_coverage: float | None
    subject_coverage: float | None
    top_hit_gene_agreement: float | None
    classification: str | None
    summary: str | None


@dataclass(frozen=True, slots=True)
class ORFView:
    available: bool
    score: float | None
    strand: str | None
    frame: int | None
    start: int | None
    end: int | None
    protein_length: int | None
    complete: bool | None
    complete_orf_count: int
    other_complete_orf_count: int
    major_competing_orf_count: int
    largest_competing_orf_length: int
    reference_id: str | None
    protein_identity: float | None
    reference_coverage: float | None
    n_terminal_missing: int | None
    c_terminal_missing: int | None
    internal_gap_residues: int | None
    internal_gap_events: int | None
    largest_internal_gap: int | None
    internal_insertion_residues: int | None
    internal_insertion_events: int | None
    largest_internal_insertion: int | None
    internal_deletion_residues: int | None
    internal_deletion_events: int | None
    largest_internal_deletion: int | None
    difference_summary: tuple[str, ...]
    interpretation_status: str | None
    interpretation_summary: str | None
    possible_frameshift_pattern: bool
    alignment_text: str | None
    predicted_protein: str | None
    reference_protein: str | None
    predicted_header: str | None
    reference_header: str | None
    predicted_coding_sequence: str | None
    predicted_coding_header: str | None
    anchored_available: bool
    anchored_protein: str | None
    anchored_coding_sequence: str | None
    anchored_protein_header: str | None
    anchored_coding_header: str | None
    anchored_start: int | None
    anchored_end: int | None
    anchored_strand: str | None
    anchored_frame: int | None
    anchored_protein_length: int | None
    anchored_complete: bool | None
    anchored_has_start: bool | None
    anchored_has_stop: bool | None
    anchored_matches_selected: bool | None
    anchored_same_start: bool | None
    anchored_same_end: bool | None
    anchored_n_terminal_difference_aa: int | None
    anchored_c_terminal_difference_aa: int | None
    warnings: tuple[str, ...]
    relatedness: ProteinRelatednessView


@dataclass(frozen=True, slots=True)
class ProteinCoordinateView:
    candidate_id: str
    subject_id: str
    subject_title: str
    subject_start: int
    subject_end: int
    subject_length: int
    start_fraction: float
    end_fraction: float
    recommended: bool


@dataclass(frozen=True, slots=True)
class ProteinContinuityView:
    classification: str
    candidate_count: int
    combined_coverage: float
    best_single_coverage: float
    complementary_candidate_ids: tuple[str, ...]
    redundant_overlap: bool
    uncovered_regions: tuple[tuple[float, float], ...]
    summary: str
    findings: tuple[str, ...]




@dataclass(frozen=True, slots=True)
class ConvergenceView:
    start: int
    end: int
    strength: str
    sources: tuple[str, ...]
    observation_types: tuple[str, ...]
    descriptions: tuple[str, ...]
    summary: str

@dataclass(frozen=True, slots=True)
class EvidenceView:
    name: str
    value: float | None
    contribution: float | None
    effective_weight: float | None




@dataclass(frozen=True, slots=True)
class RecommendationChannelView:
    name: str
    status: str
    winners: tuple[str, ...]
    recommended_value: float | None
    best_value: float


@dataclass(frozen=True, slots=True)
class CandidateComparisonView:
    candidate_id: str
    score: float
    score_gap: float
    reasons_not_selected: tuple[str, ...]
    alternative_advantages: tuple[str, ...]
    strongest_difference: str
    close_alternative: bool


@dataclass(frozen=True, slots=True)
class RecommendationView:
    candidate_id: str
    score: float
    evidence: tuple[EvidenceView, ...]
    runner_up_id: str | None
    runner_up_score: float | None
    score_gap: float | None
    runner_up_strength: str | None
    confidence: str
    supporting_channels: tuple[str, ...]
    disagreeing_channels: tuple[str, ...]
    strong_conflicts: tuple[str, ...]
    supporting_evidence: tuple[str, ...]
    opposing_evidence: tuple[str, ...]
    evidence_conflicts: tuple[str, ...]
    manual_review: bool
    assembly_review_required: bool
    assembly_level_evidence: tuple[str, ...]
    convergence_review_required: bool
    convergence_evidence: tuple[str, ...]
    recommendation_finding: str
    agreement_summary: str
    agreement_fraction: float
    channel_assessments: tuple[RecommendationChannelView, ...]
    comparisons: tuple[CandidateComparisonView, ...]
    competing_candidates: tuple[str, ...]
    unresolved_questions: tuple[str, ...]
    summary: str | None
    runner_up_reasons: tuple[str, ...]
    runner_up_advantages: tuple[str, ...]
    runner_up_strongest_difference: str | None



@dataclass(frozen=True, slots=True)
class BoundaryCoverageView:
    gap_start: int
    gap_end: int
    gap_length: int
    left_median_depth: float
    gap_median_depth: float
    right_median_depth: float
    gap_to_baseline_ratio: float | None
    zero_fraction: float
    classification: str
    severity: str
    summary: str

@dataclass(frozen=True, slots=True)
class CandidateView:
    candidate_id: str
    length: int
    confidence: float
    z: float | None
    cluster: str
    candidate_coverage: float | None
    reference_coverage: float | None
    block_count: int | None
    structural_reference_id: str | None
    longest_block_fraction: float | None
    largest_candidate_gap: int | None
    largest_reference_gap: int | None
    structural_continuity: float | None
    orientation_consistency: float | None
    order_consistency: float | None
    structural_integrity: float | None
    structural_status: str
    recommended: bool
    read_support: ReadSupportView
    orf: ORFView
    coverage_plot: str | None
    convergences: tuple[ConvergenceView, ...]
    convergence_review_required: bool
    hypotheses: tuple[HypothesisView, ...]
    boundary_coverage: tuple[BoundaryCoverageView, ...]
    scenarios: tuple[ScenarioView, ...]


@dataclass(frozen=True, slots=True)
class GenePageView:
    gene: str
    segment: str
    anchor: str | None
    recommendation: RecommendationView | None
    candidates: tuple[CandidateView, ...]
    protein_coordinates: tuple[ProteinCoordinateView, ...]
    protein_continuity: ProteinContinuityView
    hypotheses: tuple[HypothesisView, ...]
    rule_evaluations: tuple[RuleEvaluationView, ...]
    scenarios: tuple[ScenarioView, ...]


def build_recommendation_view(
    recommendation: GeneRecommendation | None,
) -> RecommendationView | None:
    if recommendation is None:
        return None

    selected = recommendation.recommended
    evidence = tuple(
        EvidenceView(
            name=name,
            value=value,
            contribution=selected.scored.contributions.get(name),
            effective_weight=selected.scored.effective_weights.get(name),
        )
        for name, value in selected.evidence.to_dict().items()
    )

    runner_up = (
        recommendation.candidates[1]
        if len(recommendation.candidates) > 1
        else None
    )

    if runner_up is None:
        score_gap = None
        runner_up_strength = None
    else:
        score_gap = selected.score - runner_up.score
        if score_gap < 0.05:
            runner_up_strength = "close"
        elif score_gap <= 0.15:
            runner_up_strength = "secondary"
        else:
            runner_up_strength = "weak"

    return RecommendationView(
        candidate_id=selected.candidate_id,
        score=selected.score,
        evidence=evidence,
        runner_up_id=runner_up.candidate_id if runner_up else None,
        runner_up_score=runner_up.score if runner_up else None,
        score_gap=score_gap,
        runner_up_strength=runner_up_strength,
        confidence=(
            recommendation.report.confidence
            if recommendation.report is not None
            else (
                recommendation.agreement.confidence
                if recommendation.agreement is not None
                else "unknown"
            )
        ),
        supporting_channels=(
            recommendation.agreement.supporting_channels
            if recommendation.agreement is not None
            else ()
        ),
        disagreeing_channels=(
            recommendation.agreement.disagreeing_channels
            if recommendation.agreement is not None
            else ()
        ),
        strong_conflicts=(
            recommendation.agreement.strong_conflicts
            if recommendation.agreement is not None
            else ()
        ),
        supporting_evidence=(
            recommendation.report.supporting_evidence
            if recommendation.report is not None
            else ()
        ),
        opposing_evidence=(
            recommendation.report.opposing_evidence
            if recommendation.report is not None
            else ()
        ),
        evidence_conflicts=(
            recommendation.report.evidence_conflicts
            if recommendation.report is not None
            else ()
        ),
        manual_review=(
            recommendation.report.manual_review
            if recommendation.report is not None
            else False
        ),
        assembly_review_required=(
            recommendation.report.assembly_review_required
            if recommendation.report is not None
            else False
        ),
        assembly_level_evidence=(
            recommendation.report.assembly_level_evidence
            if recommendation.report is not None
            else ()
        ),
        convergence_review_required=(
            recommendation.report.convergence_review_required
            if recommendation.report is not None
            else False
        ),
        convergence_evidence=(
            recommendation.report.convergence_evidence
            if recommendation.report is not None
            else ()
        ),
        recommendation_finding=(
            recommendation.report.recommendation_finding
            if recommendation.report is not None
            else "unavailable"
        ),
        agreement_summary=(
            recommendation.report.agreement_summary
            if recommendation.report is not None
            else ""
        ),
        agreement_fraction=(
            recommendation.agreement.agreement_fraction
            if recommendation.agreement is not None
            else 0.0
        ),
        channel_assessments=tuple(
            RecommendationChannelView(
                name=item.channel,
                status=item.status,
                winners=item.winners,
                recommended_value=item.recommended_value,
                best_value=item.best_value,
            )
            for item in (
                recommendation.agreement.channel_assessments
                if recommendation.agreement is not None
                else ()
            )
        ),
        comparisons=tuple(
            CandidateComparisonView(
                candidate_id=item.candidate_id,
                score=item.score,
                score_gap=item.score_gap,
                reasons_not_selected=item.reasons_not_selected,
                alternative_advantages=item.alternative_advantages,
                strongest_difference=item.strongest_difference,
                close_alternative=item.close_alternative,
            )
            for item in recommendation.comparisons
        ),
        competing_candidates=(
            recommendation.report.competing_candidates
            if recommendation.report is not None
            else ()
        ),
        unresolved_questions=(
            recommendation.report.unresolved_questions
            if recommendation.report is not None
            else ()
        ),
        summary=(
            recommendation.report.summary
            if recommendation.report is not None
            else None
        ),
        runner_up_reasons=(
            recommendation.comparisons[0].reasons_not_selected
            if recommendation.comparisons
            else ()
        ),
        runner_up_advantages=(
            recommendation.comparisons[0].alternative_advantages
            if recommendation.comparisons
            else ()
        ),
        runner_up_strongest_difference=(
            recommendation.comparisons[0].strongest_difference
            if recommendation.comparisons
            else None
        ),
    )


def build_gene_page_view(
    gene: Gene,
    recommendation: GeneRecommendation | None,
    *,
    coverage_plot_paths: dict[str, str] | None = None,
) -> GenePageView:
    coverage_plot_paths = coverage_plot_paths or {}

    recommended_id = (
        recommendation.recommended.candidate_id
        if recommendation is not None
        else None
    )

    candidates = tuple(
        CandidateView(
            candidate_id=candidate.id,
            length=candidate.length,
            confidence=float(candidate.metadata.confidence),
            z=candidate.metadata.z,
            cluster=str(candidate.metadata.cluster),
            candidate_coverage=(candidate.analysis.structural_integrity.candidate_coverage if candidate.analysis.structural_integrity is not None else None),
            reference_coverage=(candidate.analysis.structural_integrity.reference_coverage if candidate.analysis.structural_integrity is not None else None),
            block_count=(candidate.analysis.structural_integrity.block_count if candidate.analysis.structural_integrity is not None else None),
            structural_reference_id=(candidate.analysis.structural_integrity.reference_id if candidate.analysis.structural_integrity is not None else None),
            longest_block_fraction=(candidate.analysis.structural_integrity.longest_block_fraction if candidate.analysis.structural_integrity is not None else None),
            largest_candidate_gap=(candidate.analysis.structural_integrity.largest_candidate_gap if candidate.analysis.structural_integrity is not None else None),
            largest_reference_gap=(candidate.analysis.structural_integrity.largest_reference_gap if candidate.analysis.structural_integrity is not None else None),
            structural_continuity=(candidate.analysis.structural_integrity.continuity if candidate.analysis.structural_integrity is not None else None),
            orientation_consistency=(candidate.analysis.structural_integrity.orientation_consistency if candidate.analysis.structural_integrity is not None else None),
            order_consistency=(candidate.analysis.structural_integrity.order_consistency if candidate.analysis.structural_integrity is not None else None),
            structural_integrity=(candidate.analysis.structural_integrity.score if candidate.analysis.structural_integrity is not None else None),
            structural_status=(candidate.analysis.structural_integrity.status if candidate.analysis.structural_integrity is not None else "UNAVAILABLE"),
            recommended=candidate.id == recommended_id,
            read_support=build_read_support_view(candidate),
            orf=build_orf_view(candidate),
            coverage_plot=coverage_plot_paths.get(candidate.id),
            convergences=tuple(
                ConvergenceView(
                    start=item.start,
                    end=item.end,
                    strength=item.strength,
                    sources=item.sources,
                    observation_types=item.observation_types,
                    descriptions=tuple(
                        observation.description for observation in item.observations
                    ),
                    summary=item.summary,
                )
                for item in candidate.analysis.convergences
            ),
            convergence_review_required=any(
                item.strength in {"strong", "very_strong"}
                for item in candidate.analysis.convergences
            ),
            hypotheses=tuple(
                build_hypothesis_view(item)
                for item in candidate.analysis.hypotheses
            ),
            boundary_coverage=tuple(
                BoundaryCoverageView(
                    gap_start=item.gap_start,
                    gap_end=item.gap_end,
                    gap_length=item.gap_length,
                    left_median_depth=item.left_median_depth,
                    gap_median_depth=item.gap_median_depth,
                    right_median_depth=item.right_median_depth,
                    gap_to_baseline_ratio=item.gap_to_baseline_ratio,
                    zero_fraction=item.zero_fraction,
                    classification=item.classification,
                    severity=item.severity,
                    summary=item.summary,
                )
                for item in candidate.analysis.boundary_coverage
            ),
            scenarios=tuple(build_scenario_view(item) for item in candidate.analysis.scenarios),
        )
        for candidate in gene.candidates
    )

    protein_coordinates = tuple(
        ProteinCoordinateView(
            candidate_id=candidate.id,
            subject_id=candidate.analysis.blastx.subject_id,
            subject_title=candidate.analysis.blastx.subject_title,
            subject_start=min(
                candidate.analysis.blastx.subject_start,
                candidate.analysis.blastx.subject_end,
            ),
            subject_end=max(
                candidate.analysis.blastx.subject_start,
                candidate.analysis.blastx.subject_end,
            ),
            subject_length=candidate.analysis.blastx.subject_length,
            start_fraction=(
                min(
                    candidate.analysis.blastx.subject_start,
                    candidate.analysis.blastx.subject_end,
                )
                - 1
            )
            / candidate.analysis.blastx.subject_length,
            end_fraction=max(
                candidate.analysis.blastx.subject_start,
                candidate.analysis.blastx.subject_end,
            )
            / candidate.analysis.blastx.subject_length,
            recommended=candidate.id == recommended_id,
        )
        for candidate in gene.candidates
        if candidate.analysis.blastx is not None
        and candidate.analysis.blastx.subject_length > 0
    )

    continuity = analyse_protein_continuity(gene)
    recommended_hypotheses = ()
    if recommended_id is not None:
        recommended_candidate = next(
            (candidate for candidate in gene.candidates if candidate.id == recommended_id),
            None,
        )
        if recommended_candidate is not None:
            recommended_hypotheses = recommended_candidate.analysis.hypotheses

    hypotheses = tuple(
        build_hypothesis_view(item)
        for item in (*gene.hypotheses, *recommended_hypotheses)
    )

    return GenePageView(
        gene=gene.name,
        segment=gene.segment,
        anchor=gene.anchor_id,
        recommendation=build_recommendation_view(recommendation),
        candidates=candidates,
        protein_coordinates=protein_coordinates,
        hypotheses=hypotheses,
        rule_evaluations=tuple(build_rule_evaluation_view(item) for item in gene.rule_evaluations),
        scenarios=tuple(build_scenario_view(item) for item in gene.scenarios),
        protein_continuity=ProteinContinuityView(
            classification=continuity.classification,
            candidate_count=continuity.candidate_count,
            combined_coverage=continuity.combined_coverage,
            best_single_coverage=continuity.best_single_coverage,
            complementary_candidate_ids=continuity.complementary_candidate_ids,
            redundant_overlap=continuity.redundant_overlap,
            uncovered_regions=continuity.uncovered_regions,
            summary=continuity.summary,
            findings=continuity.findings,
        ),
    )


def build_read_support_view(candidate: CandidateContig) -> ReadSupportView:
    """Build ORF-centred read-evidence data for dashboard presentation."""

    metrics = candidate.analysis.read_support
    if metrics is None:
        return ReadSupportView(
            available=False,
            region_source=None,
            region_start=None,
            region_end=None,
            region_length=None,
            mean_depth=None,
            median_depth=None,
            any_covered_fraction=None,
            covered_fraction=None,
            uniformity=None,
            left_terminal_support=None,
            right_terminal_support=None,
            longest_uncovered_interval=None,
            longest_low_depth_interval=None,
            internal_low_depth_interruption_count=None,
            coverage_sufficiency=None,
            coverage_integrity=None,
            whole_contig_covered_fraction=None,
        )

    return ReadSupportView(
        available=True,
        region_source=metrics.region_source,
        region_start=metrics.region_start,
        region_end=metrics.region_end,
        region_length=metrics.region_length,
        mean_depth=metrics.mean_depth,
        median_depth=metrics.median_depth,
        any_covered_fraction=metrics.any_covered_fraction,
        covered_fraction=metrics.covered_fraction,
        uniformity=metrics.uniformity,
        left_terminal_support=metrics.left_terminal_support,
        right_terminal_support=metrics.right_terminal_support,
        longest_uncovered_interval=metrics.longest_uncovered_interval,
        longest_low_depth_interval=metrics.longest_low_depth_interval,
        internal_low_depth_interruption_count=metrics.internal_low_depth_interruption_count,
        coverage_sufficiency=metrics.coverage_sufficiency,
        coverage_integrity=metrics.coverage_integrity,
        whole_contig_covered_fraction=metrics.whole_contig_covered_fraction,
    )



def _format_protein_alignment(alignment, width: int = 60) -> str | None:
    if alignment is None or not alignment.aligned_reference:
        return None

    lines: list[str] = []
    reference_position = 0
    candidate_position = 0
    for offset in range(0, len(alignment.aligned_reference), width):
        reference = alignment.aligned_reference[offset : offset + width]
        matches = alignment.match_line[offset : offset + width]
        candidate = alignment.aligned_candidate[offset : offset + width]
        reference_start = reference_position + 1
        candidate_start = candidate_position + 1
        reference_position += sum(residue != "-" for residue in reference)
        candidate_position += sum(residue != "-" for residue in candidate)
        lines.extend(
            [
                f"Reference {reference_start:>5}  {reference}  {reference_position}",
                f"                {matches}",
                f"Candidate {candidate_start:>5}  {candidate}  {candidate_position}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _describe_protein_differences(alignment) -> tuple[str, ...]:
    if alignment is None:
        return ()

    descriptions: list[str] = []
    if alignment.n_terminal_missing:
        descriptions.append(
            f"N-terminal truncation: {alignment.n_terminal_missing} reference residues missing."
        )
    if alignment.c_terminal_missing:
        descriptions.append(
            f"C-terminal truncation: {alignment.c_terminal_missing} reference residues missing."
        )
    if alignment.internal_deletion_events:
        descriptions.append(
            f"Internal deletion: {alignment.internal_deletion_residues} residues "
            f"across {alignment.internal_deletion_events} event(s); largest "
            f"{alignment.largest_internal_deletion} aa."
        )
    if alignment.internal_insertion_events:
        descriptions.append(
            f"Internal insertion: {alignment.internal_insertion_residues} residues "
            f"across {alignment.internal_insertion_events} event(s); largest "
            f"{alignment.largest_internal_insertion} aa."
        )
    if alignment.internal_gap_events > 1:
        descriptions.append(
            "Multiple internal indel events are present; inspect for scattered "
            "differences or possible assembly error."
        )
    if not descriptions:
        descriptions.append("No terminal truncations or internal indels detected.")
    return tuple(descriptions)

def build_protein_relatedness_view(
    candidate: CandidateContig,
) -> ProteinRelatednessView:
    relatedness = candidate.analysis.protein_relatedness
    if relatedness is None:
        return ProteinRelatednessView(
            available=False,
            subject_id=None,
            subject_title=None,
            percent_identity=None,
            query_coverage=None,
            subject_coverage=None,
            top_hit_gene_agreement=None,
            classification=None,
            summary=None,
        )
    return ProteinRelatednessView(
        available=True,
        subject_id=relatedness.subject_id,
        subject_title=relatedness.subject_title,
        percent_identity=relatedness.percent_identity,
        query_coverage=relatedness.query_coverage,
        subject_coverage=relatedness.subject_coverage,
        top_hit_gene_agreement=relatedness.top_hit_gene_agreement,
        classification=relatedness.classification,
        summary=relatedness.summary,
    )


def _orf_nucleotide_sequence(candidate: CandidateContig, orf) -> str:
    sequence = candidate.record.seq[orf.start:orf.end]
    if orf.strand == "-":
        sequence = sequence.reverse_complement()
    return str(sequence).upper().replace("U", "T")


def build_orf_view(candidate: CandidateContig) -> ORFView:
    """Build ORF structural details and conservative review warnings."""

    metrics = candidate.analysis.orf
    quality = candidate.analysis.orf_quality
    alignment = candidate.analysis.orf_alignment
    interpretation = candidate.analysis.protein_interpretation
    anchored = candidate.analysis.blastx_anchored_orf

    if metrics is None or metrics.best_orf is None:
        return ORFView(
            available=False,
            score=None,
            strand=None,
            frame=None,
            start=None,
            end=None,
            protein_length=None,
            complete=None,
            complete_orf_count=0,
            other_complete_orf_count=0,
            major_competing_orf_count=0,
            largest_competing_orf_length=0,
            reference_id=None,
            protein_identity=None,
            reference_coverage=None,
            n_terminal_missing=None,
            c_terminal_missing=None,
            internal_gap_residues=None,
            internal_gap_events=None,
            largest_internal_gap=None,
            internal_insertion_residues=None,
            internal_insertion_events=None,
            largest_internal_insertion=None,
            internal_deletion_residues=None,
            internal_deletion_events=None,
            largest_internal_deletion=None,
            difference_summary=(),
            interpretation_status=None,
            interpretation_summary=None,
            possible_frameshift_pattern=False,
            alignment_text=None,
            predicted_protein=None,
            reference_protein=None,
            predicted_header=None,
            reference_header=None,
            predicted_coding_sequence=None,
            predicted_coding_header=None,
            anchored_available=False,
            anchored_protein=None,
            anchored_coding_sequence=None,
            anchored_protein_header=None,
            anchored_coding_header=None,
            anchored_start=None,
            anchored_end=None,
            anchored_strand=None,
            anchored_frame=None,
            anchored_protein_length=None,
            anchored_complete=None,
            anchored_has_start=None,
            anchored_has_stop=None,
            anchored_matches_selected=None,
            anchored_same_start=None,
            anchored_same_end=None,
            anchored_n_terminal_difference_aa=None,
            anchored_c_terminal_difference_aa=None,
            warnings=("No ORF was identified.",),
            relatedness=build_protein_relatedness_view(candidate),
        )

    best = metrics.best_orf
    warnings: list[str] = []
    if not best.complete:
        warnings.append("Best ORF is incomplete.")
    if metrics.major_competing_orf_count > 0:
        warnings.append(
            f"Major competing complete ORFs detected "
            f"({metrics.major_competing_orf_count})."
        )
    if alignment is not None:
        if alignment.reference_coverage < 0.90:
            warnings.append("Reference protein coverage is below 90%.")
        terminal_missing = (
            alignment.n_terminal_missing + alignment.c_terminal_missing
        )
        if terminal_missing > 0:
            warnings.append(
                f"Reference alignment is missing {terminal_missing} terminal residues."
            )
        if alignment.internal_gap_residues > 0:
            warnings.append(
                f"Protein alignment contains {alignment.internal_gap_residues} internal gap residues."
            )

    return ORFView(
        available=True,
        score=quality.score if quality is not None else None,
        strand=best.strand,
        frame=best.frame,
        start=best.start,
        end=best.end,
        protein_length=best.protein_length,
        complete=best.complete,
        complete_orf_count=metrics.complete_orf_count,
        other_complete_orf_count=metrics.other_complete_orf_count,
        major_competing_orf_count=metrics.major_competing_orf_count,
        largest_competing_orf_length=metrics.largest_competing_orf_length,
        reference_id=alignment.reference_id if alignment is not None else None,
        protein_identity=(
            alignment.amino_acid_identity if alignment is not None else None
        ),
        reference_coverage=(
            alignment.reference_coverage if alignment is not None else None
        ),
        n_terminal_missing=(
            alignment.n_terminal_missing if alignment is not None else None
        ),
        c_terminal_missing=(
            alignment.c_terminal_missing if alignment is not None else None
        ),
        internal_gap_residues=(
            alignment.internal_gap_residues if alignment is not None else None
        ),
        internal_gap_events=(
            alignment.internal_gap_events if alignment is not None else None
        ),
        largest_internal_gap=(
            alignment.largest_internal_gap if alignment is not None else None
        ),
        internal_insertion_residues=(
            alignment.internal_insertion_residues if alignment is not None else None
        ),
        internal_insertion_events=(
            alignment.internal_insertion_events if alignment is not None else None
        ),
        largest_internal_insertion=(
            alignment.largest_internal_insertion if alignment is not None else None
        ),
        internal_deletion_residues=(
            alignment.internal_deletion_residues if alignment is not None else None
        ),
        internal_deletion_events=(
            alignment.internal_deletion_events if alignment is not None else None
        ),
        largest_internal_deletion=(
            alignment.largest_internal_deletion if alignment is not None else None
        ),
        difference_summary=(
            interpretation.findings
            if interpretation is not None
            else _describe_protein_differences(alignment)
        ),
        interpretation_status=(
            interpretation.structural_status if interpretation is not None else None
        ),
        interpretation_summary=(
            interpretation.summary if interpretation is not None else None
        ),
        possible_frameshift_pattern=(
            interpretation.possible_frameshift_pattern
            if interpretation is not None
            else False
        ),
        alignment_text=_format_protein_alignment(alignment),
        predicted_protein=best.protein,
        reference_protein=(
            candidate.analysis.blastx.subject_protein
            if candidate.analysis.blastx is not None
            else None
        ),
        predicted_header=(
            f"{candidate.id}|selected_orf|strand={best.strand}|"
            f"frame={best.frame}|nt={best.start}-{best.end}|"
            f"length={best.protein_length}aa"
        ),
        reference_header=(
            candidate.analysis.blastx.subject_id
            if candidate.analysis.blastx is not None
            and candidate.analysis.blastx.subject_protein is not None
            else None
        ),
        predicted_coding_sequence=_orf_nucleotide_sequence(candidate, best),
        predicted_coding_header=(
            f"{candidate.id}|selected_orf_cds|strand={best.strand}|"
            f"frame={best.frame}|nt={best.start}-{best.end}|"
            f"length={best.nucleotide_length}nt"
        ),
        anchored_available=anchored is not None,
        anchored_protein=anchored.protein_sequence if anchored is not None else None,
        anchored_coding_sequence=(
            anchored.nucleotide_sequence if anchored is not None else None
        ),
        anchored_protein_header=(
            f"{candidate.id}|blastx_anchored_orf|strand={anchored.strand}|"
            f"frame={anchored.frame}|nt={anchored.start}-{anchored.end}|"
            f"start={'present' if anchored.has_start_codon else 'missing'}|"
            f"stop={'present' if anchored.has_stop_codon else 'missing'}"
            if anchored is not None else None
        ),
        anchored_coding_header=(
            f"{candidate.id}|blastx_anchored_cds|strand={anchored.strand}|"
            f"frame={anchored.frame}|nt={anchored.start}-{anchored.end}|"
            f"length={anchored.nucleotide_length}nt"
            if anchored is not None else None
        ),
        anchored_start=anchored.start if anchored is not None else None,
        anchored_end=anchored.end if anchored is not None else None,
        anchored_strand=anchored.strand if anchored is not None else None,
        anchored_frame=anchored.frame if anchored is not None else None,
        anchored_protein_length=(anchored.protein_length if anchored is not None else None),
        anchored_complete=anchored.complete if anchored is not None else None,
        anchored_has_start=(anchored.has_start_codon if anchored is not None else None),
        anchored_has_stop=(anchored.has_stop_codon if anchored is not None else None),
        anchored_matches_selected=(anchored.matches_selected_orf if anchored is not None else None),
        anchored_same_start=(anchored.same_start if anchored is not None else None),
        anchored_same_end=(anchored.same_end if anchored is not None else None),
        anchored_n_terminal_difference_aa=(
            anchored.n_terminal_difference_aa if anchored is not None else None
        ),
        anchored_c_terminal_difference_aa=(
            anchored.c_terminal_difference_aa if anchored is not None else None
        ),
        warnings=tuple(warnings),
        relatedness=build_protein_relatedness_view(candidate),
    )
