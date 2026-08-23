from __future__ import annotations

from dataclasses import dataclass, field
import base64
import json

from segpick.analysis import analyse_protein_continuity, build_evidence_assessments
from segpick.models import BiologicalHypothesis, EvidencePatternEvaluation, CandidateContig, Gene, RuleEvaluation, HypothesisEvaluation
from segpick.scoring import GeneRecommendation
from segpick.knowledge.vocabulary import ConditionDisplay, describe_condition
from itertools import combinations
from segpick.reasoning import build_llm_reasoning_bundle, build_llm_review_package, load_llm_bundle_schema, load_llm_output_schema
from segpick.explorer import ReasoningExplorer







@dataclass(frozen=True, slots=True)
class EvidencePatternEvidenceView:
    identifier: str
    display_name: str
    description: str
    source: str | None
    source_display_name: str | None
    kind: str
    graph_node_id: str | None = None
    observed_descriptions: tuple[str, ...] = ()
    measurements: tuple[dict[str, object], ...] = ()
    regions: tuple[dict[str, object], ...] = ()
    visualisations: tuple[str, ...] = ()

    @property
    def has_details(self) -> bool:
        return bool(self.observed_descriptions or self.measurements or self.regions or self.visualisations)


@dataclass(frozen=True, slots=True)
class EvidencePatternView:
    pattern_id: str
    title: str
    category: str
    scope: str
    confidence: str
    severity: str
    interpretation: str
    candidate_ids: tuple[str, ...]
    matched_required: tuple[EvidencePatternEvidenceView, ...]
    matched_supporting: tuple[EvidencePatternEvidenceView, ...]
    matched_conflicting: tuple[EvidencePatternEvidenceView, ...]
    suggested_actions: tuple[str, ...]
    source: str
    references: tuple[str, ...]
    state: str
    missing_required: tuple[EvidencePatternEvidenceView, ...]
    missing_supporting: tuple[EvidencePatternEvidenceView, ...]


def _evidence_pattern_evidence_view(
    label: str,
    provenance_by_condition: dict[str, object],
    observations: tuple[object, ...] = (),
    findings: tuple[object, ...] = (),
) -> EvidencePatternEvidenceView:
    display = describe_condition(label)
    provenance = provenance_by_condition.get(label)

    # Look up the graph node ID using the same logic as _condition_targets
    graph_node_id = None
    kind, _, remainder = label.partition(":")
    value, _, source = remainder.partition("@")
    if kind == "observation":
        for node in observations:
            if node.observation_type == value and (not source or node.source == source):
                graph_node_id = node.id
                break
    else:
        for node in findings:
            if node.title == value:
                graph_node_id = node.id
                break

    return EvidencePatternEvidenceView(
        identifier=display.identifier,
        display_name=display.display_name,
        description=display.description,
        source=display.source,
        source_display_name=display.source_display_name,
        kind=display.kind,
        graph_node_id=graph_node_id,
        observed_descriptions=tuple(getattr(provenance, "descriptions", ())),
        measurements=tuple(getattr(provenance, "measurements", ())),
        regions=tuple(getattr(provenance, "regions", ())),
        visualisations=tuple(getattr(provenance, "visualisations", ())),
    )


def build_evidence_pattern_view(item: EvidencePatternEvaluation, graph: object = None) -> EvidencePatternView:
    provenance = {entry.condition: entry for entry in item.evidence_provenance}
    observations = tuple(graph.observations) if graph else ()
    findings = tuple(graph.interpretive_findings) if graph else ()
    return EvidencePatternView(
        pattern_id=item.pattern_id,
        title=item.title,
        category=item.category,
        scope=item.scope,
        confidence=item.confidence,
        severity=item.severity,
        interpretation=item.interpretation,
        candidate_ids=item.candidate_ids,
        matched_required=tuple(_evidence_pattern_evidence_view(value, {entry.condition: entry for entry in item.evidence_provenance}, graph.observations if graph else (), graph.interpretive_findings if graph else ()) for value in item.matched_required),
        matched_supporting=tuple(_evidence_pattern_evidence_view(value, {entry.condition: entry for entry in item.evidence_provenance}, graph.observations if graph else (), graph.interpretive_findings if graph else ()) for value in item.matched_supporting),
        matched_conflicting=tuple(_evidence_pattern_evidence_view(value, {entry.condition: entry for entry in item.evidence_provenance}, graph.observations if graph else (), graph.interpretive_findings if graph else ()) for value in item.matched_conflicting),
        suggested_actions=item.suggested_actions,
        source=item.source,
        references=item.references,
        state=item.state,
        missing_required=tuple(_evidence_pattern_evidence_view(value, {entry.condition: entry for entry in item.evidence_provenance}, graph.observations if graph else (), graph.interpretive_findings if graph else ()) for value in item.missing_required),
        missing_supporting=tuple(_evidence_pattern_evidence_view(value, {entry.condition: entry for entry in item.evidence_provenance}, graph.observations if graph else (), graph.interpretive_findings if graph else ()) for value in item.missing_supporting),
    )


@dataclass(frozen=True, slots=True)
class HypothesisEvaluationView:
    hypothesis_id: str
    title: str
    category: str
    scope: str
    confidence: str
    severity: str
    explanation: str
    candidate_ids: tuple[str, ...]
    supporting_pattern_titles: tuple[str, ...]
    conflicting_pattern_titles: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    source: str
    references: tuple[str, ...]


def build_biological_hypothesis_evaluation_view(item: HypothesisEvaluation) -> HypothesisEvaluationView:
    return HypothesisEvaluationView(
        hypothesis_id=item.hypothesis_id, title=item.title, category=item.category,
        scope=item.scope, confidence=item.confidence, severity=item.severity,
        explanation=item.explanation, candidate_ids=item.candidate_ids,
        supporting_pattern_titles=item.supporting_pattern_titles,
        conflicting_pattern_titles=item.conflicting_pattern_titles,
        recommended_actions=item.recommended_actions, source=item.source,
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
class EvidenceAssessmentView:
    channel_id: str
    channel_title: str
    status: str
    score: float | None
    confidence_level: str
    confidence_score: float | None
    confidence_method: str
    confidence_version: str
    confidence_factors: tuple[dict[str, object], ...]
    limitations: tuple[str, ...]
    key_finding: str
    key_finding_description: str
    supporting_findings: tuple[str, ...]
    measurements: tuple[dict[str, object], ...]
    participates_in_ranking: bool
    diagnostics: dict[str, object] | None


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
    evidence_assessments: tuple[EvidenceAssessmentView, ...]
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
class CrossEvidenceFindingView:
    finding_id: str
    title: str
    description: str
    confidence: str
    confidence_score: float | None
    match_status: str
    evidence_completeness: float | None
    severity: str
    rule_id: str
    rule_version: str
    source_plugin: str
    supporting_evidence: tuple[str, ...]
    conflicting_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    confidence_method: str
    confidence_method_version: str
    limitations: tuple[str, ...]



@dataclass(frozen=True, slots=True)
class HypothesisInspectorView:
    hypothesis_id: str
    title: str
    summary: str
    definition_id: str
    definition_description: str
    definition_source: str
    definition_references: tuple[str, ...]
    definition_base_confidence: str
    definition_supported_by: tuple[str, ...]
    definition_contradicted_by: tuple[str, ...]
    definition_minimum_support: int
    evaluation_candidate_ids: tuple[str, ...]
    evaluation_confidence: str
    evaluation_state: str
    evaluation_supporting_synthesis_ids: tuple[str, ...]
    evaluation_conflicting_synthesis_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProvenanceStepView:
    node_id: str
    node_type: str
    title: str
    relationship: str = ""
    state: str = ""
    missing: bool = False


@dataclass(frozen=True, slots=True)
class ProvenancePathView:
    hypothesis_id: str
    hypothesis_title: str
    hypothesis_state: str
    steps: tuple[ProvenanceStepView, ...]



@dataclass(frozen=True, slots=True)
class ComparisonEvidenceView:
    """A single piece of evidence in a comparison view."""
    identifier: str
    display_name: str
    description: str
    source: str | None
    source_display_name: str | None
    kind: str
    relationship: str = ""
    graph_node_id: str | None = None
    in_a: bool = True
    in_b: bool = True

    @property
    def is_common(self) -> bool:
        return self.in_a and self.in_b

    @property
    def is_unique_to_a(self) -> bool:
        return self.in_a and not self.in_b

    @property
    def is_unique_to_b(self) -> bool:
        return self.in_b and not self.in_a


@dataclass(frozen=True, slots=True)
class ComparisonView:
    """Structural comparison of two biological hypotheses."""
    hypothesis_a_id: str
    hypothesis_a_title: str
    hypothesis_b_id: str
    hypothesis_b_title: str
    common_evidence: tuple[ComparisonEvidenceView, ...]
    unique_to_a: tuple[ComparisonEvidenceView, ...]
    unique_to_b: tuple[ComparisonEvidenceView, ...]


@dataclass(frozen=True, slots=True)
class ImpactPathView:
    """A path from an evidence node to an affected hypothesis."""
    hypothesis_id: str
    hypothesis_title: str
    hypothesis_state: str
    steps: tuple[ProvenanceStepView, ...]


@dataclass(frozen=True, slots=True)
class ImpactView:
    """Downstream consequences of an evidence node."""
    source_id: str
    source_title: str
    source_type: str
    affected_paths: tuple[ImpactPathView, ...]


@dataclass(frozen=True, slots=True)
class NextEvidenceGapView:
    """One missing piece of evidence for a hypothesis."""
    rule_id: str
    condition_label: str
    condition_kind: str  # "observation" | "finding"
    condition_value: str
    condition_source: str | None
    role: str  # "required" | "supporting"
    display_name: str
    description: str
    source_display_name: str | None


@dataclass(frozen=True, slots=True)
class NextEvidenceView:
    """Evidence gaps for a biological hypothesis."""
    hypothesis_id: str
    hypothesis_title: str
    missing_required: tuple[NextEvidenceGapView, ...]
    missing_supporting: tuple[NextEvidenceGapView, ...]

@dataclass(frozen=True, slots=True)
class ReasoningComponentView:
    component_id: str
    classification: str
    highest_level: str
    next_level: str | None
    node_count: int
    edge_count: int


@dataclass(frozen=True, slots=True)
class ReasoningGraphInspectorView:
    available: bool
    valid: bool
    validation_message: str
    measurement_count: int
    observation_count: int
    interpretation_count: int
    evidence_pattern_count: int
    hypothesis_count: int
    component_count: int
    hypothesis_component_count: int
    pattern_component_count: int
    finding_component_count: int
    observation_component_count: int
    measurement_only_component_count: int
    components: tuple[ReasoningComponentView, ...]
    builtin_sources: tuple[str, ...]
    plugin_sources: tuple[str, ...]
    provenance_paths: tuple[ProvenancePathView, ...]
    hypotheses: tuple[HypothesisInspectorView, ...]
    graph_json: str
    normalized_graph_json: str
    llm_bundle_json: str
    llm_bundle_schema_json: str
    llm_output_schema_json: str
    llm_review_package_base64: str


def build_reasoning_graph_inspector_view(candidate: CandidateContig) -> ReasoningGraphInspectorView:
    graph = candidate.analysis.reasoning_graph
    if graph is None:
        return ReasoningGraphInspectorView(
            available=False, valid=False, validation_message="Reasoning graph unavailable.",
            measurement_count=0, observation_count=0, interpretation_count=0, evidence_pattern_count=0, hypothesis_count=0,
            component_count=0, hypothesis_component_count=0, pattern_component_count=0, finding_component_count=0,
            observation_component_count=0, measurement_only_component_count=0, components=(),
            builtin_sources=(), plugin_sources=(), provenance_paths=(), hypotheses=(), graph_json="{}", normalized_graph_json="{}",
            llm_bundle_json="{}", llm_bundle_schema_json="{}", llm_output_schema_json="{}",
            llm_review_package_base64="",
        )
    try:
        graph.validate()
        valid = True
        message = "Graph validated: all referenced provenance nodes are present."
    except ValueError as exc:
        valid = False
        message = str(exc)
    sources = {item.channel for item in graph.measurements} | {item.source for item in graph.observations}
    plugin_sources = tuple(sorted(value for value in sources if value.startswith("plugin:")))
    builtin_sources = tuple(sorted(value for value in sources if not value.startswith("plugin:")))
    measurement_by_id = {item.id: item for item in graph.measurements}
    observation_by_id = {item.id: item for item in graph.observations}
    finding_by_id = {item.id: item for item in graph.interpretive_findings}
    synthesis_by_id = {item.id: item for item in graph.evidence_patterns}
    edges_by_source: dict[str, tuple[object, ...]] = {}
    for edge in graph.provenance_edges():
        edges_by_source.setdefault(edge.source_id, ())
        edges_by_source[edge.source_id] += (edge,)

    def linked_edges(node_id: str) -> tuple[object, ...]:
        return edges_by_source.get(node_id, ())

    def missing_step(node_id: str, relationship: str) -> ProvenanceStepView:
        return ProvenanceStepView(
            node_id=node_id, node_type="missing", title="Missing graph node",
            relationship=relationship, missing=True,
        )

    def evidence_paths(
        evidence_id: str,
        relationship: str,
        visited: frozenset[str] = frozenset(),
    ) -> tuple[tuple[ProvenanceStepView, ...], ...]:
        if evidence_id in visited:
            return ((ProvenanceStepView(
                node_id=evidence_id, node_type="cycle", title="Cycle detected",
                relationship=relationship, missing=True,
            ),),)
        visited = visited | {evidence_id}
        if evidence_id in finding_by_id:
            finding = finding_by_id[evidence_id]
            head = ProvenanceStepView(
                node_id=finding.id, node_type="interpretive finding", title=finding.title,
                relationship=relationship, state=finding.state,
            )
            links = [
                (edge.target_id, edge.relationship.replace("_", " "))
                for edge in linked_edges(finding.id)
            ]
            if not links:
                return ((head, missing_step(finding.id, "no evidence link")),)
            return tuple(
                (head, *tail)
                for nested_id, nested_relation in links
                for tail in evidence_paths(nested_id, nested_relation, visited)
            )
        if evidence_id in observation_by_id:
            observation = observation_by_id[evidence_id]
            head = ProvenanceStepView(
                node_id=observation.id, node_type="observation",
                title=observation.description, relationship=relationship,
                state=observation.severity,
            )
            measurement_edges = linked_edges(observation.id)
            if not measurement_edges:
                return ((head,),)
            paths = []
            for edge in measurement_edges:
                measurement_id = edge.target_id
                measurement = measurement_by_id.get(measurement_id)
                if measurement is None:
                    paths.append((head, missing_step(measurement_id, "supported by")))
                else:
                    value = measurement.value
                    if measurement.unit:
                        value = f"{value} {measurement.unit}"
                    paths.append((head, ProvenanceStepView(
                        node_id=measurement.id, node_type="measurement",
                        title=f"{measurement.name}: {value}", relationship=edge.relationship.replace("_", " "),
                        state=measurement.channel,
                    )))
            return tuple(paths)
        if evidence_id in measurement_by_id:
            measurement = measurement_by_id[evidence_id]
            value = measurement.value
            if measurement.unit:
                value = f"{value} {measurement.unit}"
            return ((ProvenanceStepView(
                node_id=measurement.id, node_type="measurement",
                title=f"{measurement.name}: {value}", relationship=relationship,
                state=measurement.channel,
            ),),)
        return ((missing_step(evidence_id, relationship),),)

    paths: list[ProvenancePathView] = []
    for hypothesis in graph.biological_hypotheses:
        hypothesis_step = ProvenanceStepView(
            node_id=hypothesis.id, node_type="biological hypothesis",
            title=hypothesis.title, state=hypothesis.state,
        )
        hypothesis_links = [
            (edge.target_id, edge.relationship.replace("_", " "))
            for edge in linked_edges(hypothesis.id)
        ]
        if not hypothesis_links:
            paths.append(ProvenancePathView(
                hypothesis_id=hypothesis.id, hypothesis_title=hypothesis.title,
                hypothesis_state=hypothesis.state,
                steps=(hypothesis_step, missing_step(hypothesis.id, "no evidence link")),
            ))
            continue
        for evidence_id, relation in hypothesis_links:
            if evidence_id in synthesis_by_id:
                synthesis = synthesis_by_id[evidence_id]
                synthesis_step = ProvenanceStepView(
                    node_id=synthesis.id, node_type="evidence synthesis",
                    title=synthesis.title, relationship=relation, state=synthesis.confidence,
                )
                synthesis_links = [
                    (edge.target_id, edge.relationship.replace("_", " "))
                    for edge in linked_edges(synthesis.id)
                ]
                if not synthesis_links:
                    paths.append(ProvenancePathView(
                        hypothesis_id=hypothesis.id, hypothesis_title=hypothesis.title,
                        hypothesis_state=hypothesis.state,
                        steps=(hypothesis_step, synthesis_step, missing_step(synthesis.id, "no evidence link")),
                    ))
                else:
                    for nested_id, nested_relation in synthesis_links:
                        for tail in evidence_paths(nested_id, nested_relation):
                            paths.append(ProvenancePathView(
                                hypothesis_id=hypothesis.id, hypothesis_title=hypothesis.title,
                                hypothesis_state=hypothesis.state,
                                steps=(hypothesis_step, synthesis_step, *tail),
                            ))
            else:
                for tail in evidence_paths(evidence_id, relation):
                    paths.append(ProvenancePathView(
                        hypothesis_id=hypothesis.id, hypothesis_title=hypothesis.title,
                        hypothesis_state=hypothesis.state,
                        steps=(hypothesis_step, *tail),
                    ))
    component_models = graph.reasoning_components() if valid else ()
    component_views = tuple(ReasoningComponentView(
        component_id=item.component_id, classification=item.classification,
        highest_level=item.highest_level, next_level=item.next_level,
        node_count=item.node_count, edge_count=item.edge_count,
    ) for item in component_models)
    component_counts: dict[str, int] = {}
    for item in component_models:
        component_counts[item.classification] = component_counts.get(item.classification, 0) + 1

    hypothesis_views = tuple(
        HypothesisInspectorView(
            hypothesis_id=item.id,
            title=item.title,
            summary=item.summary,
            definition_id=item.definition_id or item.rule_id,
            definition_description=item.rule_description,
            definition_source=item.rule_source,
            definition_references=item.rule_references,
            definition_base_confidence=item.definition_base_confidence,
            definition_supported_by=item.definition_supported_by,
            definition_contradicted_by=item.definition_contradicted_by,
            definition_minimum_support=item.definition_minimum_support,
            evaluation_candidate_ids=item.evaluation_candidate_ids,
            evaluation_confidence=item.confidence,
            evaluation_state=item.state,
            evaluation_supporting_synthesis_ids=item.evaluation_supporting_synthesis_ids,
            evaluation_conflicting_synthesis_ids=item.evaluation_conflicting_synthesis_ids,
        )
        for item in graph.biological_hypotheses
    )
    graph_json = json.dumps(graph.to_dict(), indent=2, sort_keys=True) if valid else "{}"
    normalized_graph_json = json.dumps(graph.to_normalized_dict(), indent=2, sort_keys=True) if valid else "{}"
    if valid:
        llm_bundle = build_llm_reasoning_bundle(graph, candidate_id=candidate.id)
        llm_bundle_schema = load_llm_bundle_schema()
        llm_output_schema = load_llm_output_schema()
        llm_bundle_json = json.dumps(llm_bundle, indent=2, sort_keys=True)
        llm_bundle_schema_json = json.dumps(llm_bundle_schema, indent=2, sort_keys=True)
        llm_output_schema_json = json.dumps(llm_output_schema, indent=2, sort_keys=True)
        llm_review_package_base64 = base64.b64encode(
            build_llm_review_package(graph, candidate_id=candidate.id)
        ).decode("ascii")
    else:
        llm_bundle_json = "{}"
        llm_bundle_schema_json = "{}"
        llm_output_schema_json = "{}"
        llm_review_package_base64 = ""
    return ReasoningGraphInspectorView(
        available=True, valid=valid, validation_message=message,
        measurement_count=len(graph.measurements), observation_count=len(graph.observations),
        interpretation_count=len(graph.interpretive_findings), evidence_pattern_count=len(graph.evidence_patterns),
        hypothesis_count=len(graph.biological_hypotheses),
        component_count=len(component_models),
        hypothesis_component_count=component_counts.get("hypothesis_provenance", 0),
        pattern_component_count=component_counts.get("unresolved_evidence_pattern", 0),
        finding_component_count=component_counts.get("unresolved_interpretive_finding", 0),
        observation_component_count=component_counts.get("observation_only", 0),
        measurement_only_component_count=component_counts.get("measurement_only", 0),
        components=component_views,
        builtin_sources=builtin_sources, plugin_sources=plugin_sources,
        provenance_paths=tuple(paths), hypotheses=hypothesis_views,
        graph_json=graph_json, normalized_graph_json=normalized_graph_json,
        llm_bundle_json=llm_bundle_json,
        llm_bundle_schema_json=llm_bundle_schema_json,
        llm_output_schema_json=llm_output_schema_json,
        llm_review_package_base64=llm_review_package_base64,
    )




# --- Comparison / Impact / Next Evidence build functions ---

def _node_to_comparison_evidence(
    node,
    edges: tuple[object, ...],
    in_a: bool,
    in_b: bool,
) -> ComparisonEvidenceView:
    """Convert a graph node to a ComparisonEvidenceView."""
    # Determine display name and kind from node type
    if hasattr(node, 'pattern_id'):  # EvidencePatternNode
        kind = "evidence_pattern"
        display_name = node.title
        description = node.interpretation
        source = node.source
    elif hasattr(node, 'observation_type'):  # ObservationNode
        kind = "observation"
        display_name = node.observation_type.replace("_", " ").title()
        description = node.description
        source = node.source
    elif hasattr(node, 'title'):  # InterpretiveFindingNode or BiologicalHypothesisNode
        if hasattr(node, 'hypothesis_type'):  # BiologicalHypothesisNode
            kind = "biological_hypothesis"
        else:
            kind = "interpretive_finding"
        display_name = node.title
        description = node.summary
        source = getattr(node, 'source', getattr(node, 'rule_source', ''))
    else:
        kind = "measurement"
        display_name = node.name
        description = f"Measurement: {node.value}"
        source = node.channel

    return ComparisonEvidenceView(
        identifier=node.id,
        display_name=display_name,
        description=description,
        source=source,
        source_display_name=source.replace("_", " ").title() if source else None,
        kind=kind,
        in_a=in_a,
        in_b=in_b,
    )


def build_comparison_view(
    explorer,
    hypothesis_a_id: str,
    hypothesis_b_id: str,
) -> ComparisonView:
    """Build a comparison view from two hypothesis nodes."""
    prov_a = explorer.explain(hypothesis_a_id)
    prov_b = explorer.explain(hypothesis_b_id)

    # Get node IDs
    nodes_a = {n.id: n for n in prov_a.nodes}
    nodes_b = {n.id: n for n in prov_b.nodes}
    edges_a = {(e.source_id, e.target_id, e.relationship): e for e in prov_a.edges}
    edges_b = {(e.source_id, e.target_id, e.relationship): e for e in prov_b.edges}

    common_node_ids = set(nodes_a.keys()) & set(nodes_b.keys())
    unique_a_node_ids = set(nodes_a.keys()) - set(nodes_b.keys())
    unique_b_node_ids = set(nodes_b.keys()) - set(nodes_a.keys())

    # Build comparison evidence views
    common_evidence = []
    for nid in sorted(common_node_ids):
        node = nodes_a[nid]
        # Find edges for this node in both provenances
        rel_a = next((e.relationship for e in prov_a.edges if e.source_id == nid or e.target_id == nid), "")
        rel_b = next((e.relationship for e in prov_b.edges if e.source_id == nid or e.target_id == nid), "")
        rel = rel_a or rel_b
        common_evidence.append(ComparisonEvidenceView(
            identifier=node.id,
            display_name=node.title if hasattr(node, 'title') else node.observation_type if hasattr(node, 'observation_type') else node.name,
            description=node.summary if hasattr(node, 'summary') else node.description if hasattr(node, 'description') else node.interpretation if hasattr(node, 'interpretation') else "",
            source=node.source if hasattr(node, 'source') else node.channel if hasattr(node, 'channel') else "",
            source_display_name=(node.source if hasattr(node, 'source') else node.channel if hasattr(node, 'channel') else "").replace("_", " ").title(),
            kind="biological_hypothesis" if hasattr(node, 'hypothesis_type') else "evidence_pattern" if hasattr(node, 'pattern_id') else "interpretive_finding" if hasattr(node, 'source') and node.source == "finding" else "observation" if hasattr(node, 'observation_type') else "measurement",
            relationship=rel.replace("_", " "),
            graph_node_id=node.id,
            in_a=True,
            in_b=True,
        ))

    unique_to_a = []
    for nid in sorted(unique_a_node_ids):
        node = nodes_a[nid]
        rel = next((e.relationship for e in prov_a.edges if e.source_id == nid or e.target_id == nid), "")
        unique_to_a.append(ComparisonEvidenceView(
            identifier=node.id,
            display_name=node.title if hasattr(node, 'title') else node.observation_type if hasattr(node, 'observation_type') else node.name,
            description=node.summary if hasattr(node, 'summary') else node.description if hasattr(node, 'description') else node.interpretation if hasattr(node, 'interpretation') else "",
            source=node.source if hasattr(node, 'source') else node.channel if hasattr(node, 'channel') else "",
            source_display_name=(node.source if hasattr(node, 'source') else node.channel if hasattr(node, 'channel') else "").replace("_", " ").title(),
            kind="biological_hypothesis" if hasattr(node, 'hypothesis_type') else "evidence_pattern" if hasattr(node, 'pattern_id') else "interpretive_finding" if hasattr(node, 'source') and node.source == "finding" else "observation" if hasattr(node, 'observation_type') else "measurement",
            relationship=rel.replace("_", " "),
            in_a=True,
            in_b=False,
        ))

    unique_to_b = []
    for nid in sorted(unique_b_node_ids):
        node = nodes_b[nid]
        rel = next((e.relationship for e in prov_b.edges if e.source_id == nid or e.target_id == nid), "")
        unique_to_b.append(ComparisonEvidenceView(
            identifier=node.id,
            display_name=node.title if hasattr(node, 'title') else node.observation_type if hasattr(node, 'observation_type') else node.name,
            description=node.summary if hasattr(node, 'summary') else node.description if hasattr(node, 'description') else node.interpretation if hasattr(node, 'interpretation') else "",
            source=node.source if hasattr(node, 'source') else node.channel if hasattr(node, 'channel') else "",
            source_display_name=(node.source if hasattr(node, 'source') else node.channel if hasattr(node, 'channel') else "").replace("_", " ").title(),
            kind="biological_hypothesis" if hasattr(node, 'hypothesis_type') else "evidence_pattern" if hasattr(node, 'pattern_id') else "interpretive_finding" if hasattr(node, 'source') and node.source == "finding" else "observation" if hasattr(node, 'observation_type') else "measurement",
            relationship=rel.replace("_", " "),
            graph_node_id=node.id,
            in_a=False,
            in_b=True,
        ))

    return ComparisonView(
        hypothesis_a_id=prov_a.claim.id,
        hypothesis_a_title=prov_a.claim.title,
        hypothesis_b_id=prov_b.claim.id,
        hypothesis_b_title=prov_b.claim.title,
        common_evidence=tuple(common_evidence),
        unique_to_a=tuple(unique_to_a),
        unique_to_b=tuple(unique_to_b),
    )


def build_impact_view(
    explorer,
    node_id: str,
) -> ImpactView:
    """Build an impact view from an evidence node."""
    result = explorer.impact(node_id)
    source = result.source

    source_title = source.title if hasattr(source, 'title') else source.observation_type if hasattr(source, 'observation_type') else source.name
    source_type = "biological_hypothesis" if hasattr(source, 'hypothesis_type') else "evidence_pattern" if hasattr(source, 'pattern_id') else "interpretive_finding" if hasattr(source, 'source') and source.source == "finding" else "observation" if hasattr(source, 'observation_type') else "measurement"

    affected_paths = []
    for path in result.paths:
        steps = []
        for i, (node, edge) in enumerate(zip(path.nodes, path.edges)):
            # Create ProvenanceStepView for each step
            if i == 0:
                # First step - the source node
                step_node = node
            else:
                step_node = node

            step_title = step_node.title if hasattr(step_node, 'title') else step_node.observation_type if hasattr(step_node, 'observation_type') else step_node.name
            step_type = "biological_hypothesis" if hasattr(step_node, 'hypothesis_type') else "evidence_pattern" if hasattr(step_node, 'pattern_id') else "interpretive_finding" if hasattr(step_node, 'source') and step_node.source == "finding" else "observation" if hasattr(step_node, 'observation_type') else "measurement"
            step_state = getattr(step_node, 'state', getattr(step_node, 'confidence', getattr(step_node, 'severity', '')))

            steps.append(ProvenanceStepView(
                node_id=step_node.id,
                node_type=step_type,
                title=step_title,
                relationship=edge.relationship.replace("_", " ") if i > 0 else "",
                state=step_state,
            ))

        # Add final claim step
        claim = path.claim
        claim_title = claim.title
        claim_state = claim.state if hasattr(claim, 'state') else claim.confidence if hasattr(claim, 'confidence') else ''
        steps.append(ProvenanceStepView(
            node_id=claim.id,
            node_type="biological_hypothesis",
            title=claim_title,
            relationship=path.edges[-1].relationship.replace("_", " ") if path.edges else "",
            state=claim_state,
        ))

        affected_paths.append(ImpactPathView(
            hypothesis_id=claim.id,
            hypothesis_title=claim_title,
            hypothesis_state=claim_state,
            steps=tuple(steps),
        ))

    return ImpactView(
        source_id=source.id,
        source_title=source_title,
        source_type=source_type,
        affected_paths=tuple(affected_paths),
    )


def build_next_evidence_view(
    explorer,
    hypothesis_id: str,
) -> NextEvidenceView:
    """Build a next evidence view from a hypothesis node."""
    result = explorer.next_evidence(hypothesis_id)
    hypothesis = result.hypothesis

    missing_required = []
    for gap in result.missing_required:
        cond = gap.condition
        # Use vocabulary to get display name
        from segpick.knowledge.vocabulary import describe_condition
        display = describe_condition(cond.label)
        missing_required.append(NextEvidenceGapView(
            rule_id=gap.rule_id,
            condition_label=cond.label,
            condition_kind=cond.kind,
            condition_value=cond.value,
            condition_source=cond.source,
            role=gap.role,
            display_name=display.display_name,
            description=display.description,
            source_display_name=display.source_display_name,
        ))

    missing_supporting = []
    for gap in result.missing_supporting:
        cond = gap.condition
        from segpick.knowledge.vocabulary import describe_condition
        display = describe_condition(cond.label)
        missing_supporting.append(NextEvidenceGapView(
            rule_id=gap.rule_id,
            condition_label=cond.label,
            condition_kind=cond.kind,
            condition_value=cond.value,
            condition_source=cond.source,
            role=gap.role,
            display_name=display.display_name,
            description=display.description,
            source_display_name=display.source_display_name,
        ))

    return NextEvidenceView(
        hypothesis_id=hypothesis.id,
        hypothesis_title=hypothesis.title,
        missing_required=tuple(missing_required),
        missing_supporting=tuple(missing_supporting),
    )



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
    reference_compatibility: float | None
    reference_compatibility_status: str
    unsupported_internal_candidate_bases: int | None
    missing_internal_reference_bases: int | None
    duplicated_reference_bases: int | None
    expected_reference_completeness: float | None
    reference_block_order_compatibility: float | None
    reference_orientation_compatibility: float | None
    duplication_compatibility: float | None
    recommended: bool
    read_support: ReadSupportView
    orf: ORFView
    coverage_plot: str | None
    convergences: tuple[ConvergenceView, ...]
    convergence_review_required: bool
    hypotheses: tuple[HypothesisView, ...]
    boundary_coverage: tuple[BoundaryCoverageView, ...]
    evidence_patterns: tuple[EvidencePatternView, ...]
    unresolved_evidence_patterns: tuple[EvidencePatternView, ...]
    biological_hypothesis_evaluations: tuple[HypothesisEvaluationView, ...]
    cross_evidence_findings: tuple[CrossEvidenceFindingView, ...]
    reasoning_graph: ReasoningGraphInspectorView
    next_evidence_views: dict[str, NextEvidenceView]
    impact_views: dict[str, ImpactView]
    comparison_views: dict[tuple[str, str], ComparisonView] = field(default_factory=dict)


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
    evidence_patterns: tuple[EvidencePatternView, ...]
    biological_hypothesis_evaluations: tuple[HypothesisEvaluationView, ...]


def build_recommendation_view(
    recommendation: GeneRecommendation | None,
    candidate: CandidateContig | None = None,
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
        evidence_assessments=tuple(
            EvidenceAssessmentView(
                channel_id=item.channel_id, channel_title=item.channel_title, status=item.status, score=item.score,
                confidence_level=item.confidence.level, confidence_score=item.confidence.score,
                confidence_method=item.confidence.method, confidence_version=item.confidence.version,
                confidence_factors=tuple(factor.to_dict() for factor in item.confidence.factors),
                limitations=item.limitations, key_finding=item.key_finding.title,
                key_finding_description=item.key_finding.description,
                supporting_findings=tuple(value.title for value in item.supporting_findings),
                measurements=item.measurements, participates_in_ranking=item.participates_in_ranking,
                diagnostics=item.diagnostics.to_dict() if item.diagnostics is not None else None,
            )
            for item in (build_evidence_assessments(candidate, selected) if candidate is not None else ())
        ),
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


def build_next_evidence_views(candidate: CandidateContig) -> dict[str, NextEvidenceView]:
    """Build NextEvidenceView for each biological hypothesis evaluation."""
    graph = candidate.analysis.reasoning_graph
    if graph is None:
        return {}

    explorer = ReasoningExplorer(graph)
    views = {}

    for hyp_eval in candidate.analysis.biological_hypothesis_evaluations:
        graph_hypothesis = next(
            (h for h in graph.biological_hypotheses if h.rule_id == hyp_eval.hypothesis_id),
            None
        )
        if graph_hypothesis:
            try:
                views[hyp_eval.hypothesis_id] = build_next_evidence_view(explorer, graph_hypothesis.id)
            except KeyError:
                pass

    return views


def build_impact_views(candidate: CandidateContig) -> dict[str, ImpactView]:
    """Build ImpactView for key evidence nodes in the reasoning graph."""
    graph = candidate.analysis.reasoning_graph
    if graph is None:
        return {}

    explorer = ReasoningExplorer(graph)
    views = {}

    for node in graph.observations:
        try:
            views[node.id] = build_impact_view(explorer, node.id)
        except KeyError:
            pass

    for node in graph.interpretive_findings:
        try:
            views[node.id] = build_impact_view(explorer, node.id)
        except KeyError:
            pass

    for node in graph.evidence_patterns:
        try:
            views[node.id] = build_impact_view(explorer, node.id)
        except KeyError:
            pass

    return views


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
            reference_compatibility=(candidate.analysis.reference_compatibility.score if candidate.analysis.reference_compatibility is not None else None),
            reference_compatibility_status=(candidate.analysis.reference_compatibility.status if candidate.analysis.reference_compatibility is not None else "UNAVAILABLE"),
            unsupported_internal_candidate_bases=(candidate.analysis.reference_compatibility.unsupported_internal_candidate_bases if candidate.analysis.reference_compatibility is not None else None),
            missing_internal_reference_bases=(candidate.analysis.reference_compatibility.missing_internal_reference_bases if candidate.analysis.reference_compatibility is not None else None),
            duplicated_reference_bases=(candidate.analysis.reference_compatibility.duplicated_reference_bases if candidate.analysis.reference_compatibility is not None else None),
            expected_reference_completeness=(candidate.analysis.reference_compatibility.expected_reference_completeness if candidate.analysis.reference_compatibility is not None else None),
            reference_block_order_compatibility=(candidate.analysis.reference_compatibility.block_order_compatibility if candidate.analysis.reference_compatibility is not None else None),
            reference_orientation_compatibility=(candidate.analysis.reference_compatibility.orientation_compatibility if candidate.analysis.reference_compatibility is not None else None),
            duplication_compatibility=(candidate.analysis.reference_compatibility.duplication_compatibility if candidate.analysis.reference_compatibility is not None else None),
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
            evidence_patterns=tuple(build_evidence_pattern_view(item, candidate.analysis.reasoning_graph) for item in candidate.analysis.evidence_patterns),
            unresolved_evidence_patterns=tuple(build_evidence_pattern_view(item, candidate.analysis.reasoning_graph) for item in candidate.analysis.unresolved_evidence_patterns),
            biological_hypothesis_evaluations=tuple(build_biological_hypothesis_evaluation_view(item) for item in candidate.analysis.biological_hypothesis_evaluations),
            cross_evidence_findings=tuple(
                CrossEvidenceFindingView(
                    finding_id=item.finding_id,
                    title=item.title,
                    description=item.description,
                    confidence=item.confidence,
                    confidence_score=item.confidence_score,
                    match_status=item.match_status,
                    evidence_completeness=item.evidence_completeness,
                    severity=item.severity,
                    rule_id=item.rule_id,
                    rule_version=item.rule_version,
                    source_plugin=item.source_plugin,
                    supporting_evidence=tuple(ref.title for ref in item.supporting_evidence),
                    conflicting_evidence=tuple(ref.title for ref in item.conflicting_evidence),
                    missing_evidence=tuple(item.title for item in item.missing_contributions),
                    confidence_method=item.confidence_method,
                    confidence_method_version=item.confidence_method_version,
                    limitations=item.limitations,
                )
                for item in candidate.analysis.cross_evidence_findings
            ),
            reasoning_graph=build_reasoning_graph_inspector_view(candidate),
            next_evidence_views=build_next_evidence_views(candidate),
            impact_views=build_impact_views(candidate),
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
        recommendation=build_recommendation_view(recommendation, next((item for item in gene.candidates if item.id == recommended_id), None)),
        candidates=candidates,
        protein_coordinates=protein_coordinates,
        hypotheses=hypotheses,
        rule_evaluations=tuple(build_rule_evaluation_view(item) for item in gene.rule_evaluations),
        evidence_patterns=tuple(build_evidence_pattern_view(item) for item in gene.evidence_patterns),
        biological_hypothesis_evaluations=tuple(build_biological_hypothesis_evaluation_view(item) for item in gene.biological_hypothesis_evaluations),
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
