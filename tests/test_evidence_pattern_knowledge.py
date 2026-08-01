from pathlib import Path

from segpick.cli import build_parser
from segpick.config import resolve_config
from segpick.knowledge import evaluate_evidence_patterns, load_active_evidence_patterns
from segpick.models import BiologicalFinding, EvidenceObservation, ObservationSource


def test_builtin_knowledge_modules_load_by_scope():
    candidate, gene = load_active_evidence_patterns()
    assert any(item.pattern_id == "coverage_supported_assembly_breakpoint" for item in candidate)
    assert any(item.pattern_id == "complementary_fragmented_gene" for item in gene)


def test_pattern_evaluation_is_traceable_and_suggests_actions():
    candidate, _ = load_active_evidence_patterns()
    observations = (
        EvidenceObservation(
            observation_type="reference_structural_discontinuity",
            source=ObservationSource.STRUCTURAL_ALIGNMENT,
            description="break",
        ),
        EvidenceObservation(
            observation_type="coverage_drop_at_reference_boundary",
            source=ObservationSource.CROSS_EVIDENCE,
            description="drop",
        ),
        EvidenceObservation(
            observation_type="internal_coverage_interruption",
            source=ObservationSource.READ_COVERAGE,
            description="gap",
        ),
    )
    patterns = evaluate_evidence_patterns(candidate, observations, (), candidate_ids=("c1",))
    pattern = next(item for item in patterns if item.pattern_id == "coverage_supported_assembly_breakpoint")
    assert pattern.confidence == "high"
    assert pattern.candidate_ids == ("c1",)
    assert pattern.matched_required
    assert pattern.suggested_actions
    assert pattern.to_dict()["source"] == "builtin:default_evidence_patterns.yml"


def test_user_knowledge_file_and_cli_override(tmp_path: Path):
    path = tmp_path / "knowledge.yml"
    path.write_text(
        """version: 1
evidence_patterns:
  - id: custom_case
    title: Custom case
    category: test
    scope: candidate
    severity: informational
    base_confidence: low
    interpretation: A custom laboratory interpretation.
    requires:
      - finding: Complete protein recovered
    suggested_actions:
      - Review the custom case.
"""
    )
    candidate, _ = load_active_evidence_patterns((path,))
    assert any(item.pattern_id == "custom_case" and item.source == str(path) for item in candidate)

    args = build_parser().parse_args(["run", "--knowledge-file", str(path)])
    assert args.knowledge_files == [str(path)]
    config = resolve_config({}, {"knowledge_files": args.knowledge_files})
    assert config.knowledge_files == (path,)


def test_pattern_view_uses_human_friendly_observation_text():
    from segpick.models import EvidencePatternEvaluation
    from segpick.reporting.view_models import build_evidence_pattern_view

    pattern = EvidencePatternEvaluation(
        pattern_id="incomplete_terminal_assembly",
        title="Possible incomplete terminal assembly",
        category="completeness",
        scope="candidate",
        confidence="moderate",
        severity="review",
        interpretation="Possible truncation.",
        matched_required=("observation:weak_orf_terminal_support@read_coverage",),
    )
    view = build_evidence_pattern_view(pattern)
    condition = view.matched_required[0]
    assert condition.display_name == "Weak ORF terminal support"
    assert condition.source_display_name == "Read coverage"
    assert "predicted coding sequence" in condition.description
    assert condition.identifier == "observation:weak_orf_terminal_support@read_coverage"


def test_unknown_observation_gets_readable_fallback():
    from segpick.knowledge import describe_condition

    condition = describe_condition("observation:new_laboratory_signal@custom_source")
    assert condition.display_name == "New laboratory signal"
    assert condition.source_display_name == "Custom source"


def test_pattern_provenance_records_measurements_regions_and_visualisations():
    candidate, _ = load_active_evidence_patterns()
    observations = (
        EvidenceObservation(
            observation_type="reference_structural_discontinuity",
            source=ObservationSource.STRUCTURAL_ALIGNMENT,
            description="Two alignment blocks are separated by 318 nt.",
            coordinate_system="candidate:c1",
            start=1201,
            end=1518,
            attributes={"hsp_count": 2, "gap_length": 318},
        ),
        EvidenceObservation(
            observation_type="coverage_drop_at_reference_boundary",
            source=ObservationSource.CROSS_EVIDENCE,
            description="Median depth falls from 84x to 11x at the boundary.",
            attributes={"baseline_depth": 84.0, "boundary_depth": 11.0, "depth_ratio": 0.131},
        ),
    )
    pattern = next(
        item for item in evaluate_evidence_patterns(candidate, observations, (), candidate_ids=("c1",))
        if item.pattern_id == "coverage_supported_assembly_breakpoint"
    )
    assert len(pattern.evidence_provenance) == 2
    structural = next(item for item in pattern.evidence_provenance if item.source == "structural_alignment")
    assert structural.descriptions == ("Two alignment blocks are separated by 318 nt.",)
    assert {item["name"] for item in structural.measurements} == {"gap_length", "hsp_count"}
    assert structural.regions[0]["start"] == 1201
    assert "reference_dotplot" in structural.visualisations
    payload = pattern.to_dict()
    assert payload["evidence_provenance"][0]["condition"].startswith("observation:")


def test_pattern_dashboard_uses_collapsed_nested_provenance(tmp_path):
    from segpick.reporting.html_report import write_html_dashboard
    from tests.test_recommendation_reporting import make_sample

    sample, recommendations = make_sample()
    candidate, _ = load_active_evidence_patterns()
    contig = sample.genes["VP2"].candidates[0]
    contig.analysis.observations = (
        EvidenceObservation(
            observation_type="reference_structural_discontinuity",
            source=ObservationSource.STRUCTURAL_ALIGNMENT,
            description="Two structural blocks.",
            attributes={"hsp_count": 2},
        ),
        EvidenceObservation(
            observation_type="coverage_drop_at_reference_boundary",
            source=ObservationSource.CROSS_EVIDENCE,
            description="Depth decreases at the boundary.",
            attributes={"depth_ratio": 0.2},
        ),
    )
    contig.analysis.evidence_patterns = evaluate_evidence_patterns(candidate, contig.analysis.observations, (), candidate_ids=(contig.id,))
    write_html_dashboard(sample, tmp_path, recommendations)
    html = (tmp_path / "genes" / "VP2.html").read_text()
    assert '<details class="hypothesis-item evidence-pattern-item">' in html
    assert '<details class="provenance-item">' in html
    assert "Measurements" in html
    assert "Examine evidence" in html
    assert "observation:reference_structural_discontinuity" not in html


def test_reference_compatibility_patterns_distinguish_supported_and_unsupported_insertions():
    candidate, _ = load_active_evidence_patterns()
    supported_observations = (
        EvidenceObservation(
            observation_type="unsupported_internal_candidate_region",
            source=ObservationSource.REFERENCE_COMPATIBILITY,
            description="343 nt absent from reference.",
            attributes={"unsupported_internal_candidate_bases": 343},
        ),
        EvidenceObservation(
            observation_type="complete_orf_read_coverage",
            source=ObservationSource.READ_COVERAGE,
            description="ORF is covered.",
        ),
    )
    supported = evaluate_evidence_patterns(candidate, supported_observations, (), candidate_ids=("c1",))
    ids = {item.pattern_id for item in supported}
    assert "reference_unsupported_internal_sequence" in ids
    assert "coverage_supported_reference_insertion" in ids
    assert "possible_misassembled_internal_insertion" not in ids

    interrupted_observations = (
        supported_observations[0],
        EvidenceObservation(
            observation_type="internal_coverage_interruption",
            source=ObservationSource.READ_COVERAGE,
            description="Coverage interruption inside interval.",
        ),
    )
    interrupted = evaluate_evidence_patterns(candidate, interrupted_observations, (), candidate_ids=("c1",))
    ids = {item.pattern_id for item in interrupted}
    assert "possible_misassembled_internal_insertion" in ids
    generic = next(item for item in interrupted if item.pattern_id == "reference_unsupported_internal_sequence")
    assert generic.confidence == "low"


def test_reference_compatibility_patterns_cover_order_orientation_duplication_and_loss():
    candidate, _ = load_active_evidence_patterns()
    observations = (
        EvidenceObservation("reference_block_order_disrupted", ObservationSource.REFERENCE_COMPATIBILITY, "order"),
        EvidenceObservation("unexpected_reference_orientation_switch", ObservationSource.REFERENCE_COMPATIBILITY, "orientation"),
        EvidenceObservation("duplicated_reference_mapping", ObservationSource.REFERENCE_COMPATIBILITY, "duplication"),
        EvidenceObservation("missing_expected_reference_region", ObservationSource.REFERENCE_COMPATIBILITY, "loss"),
    )
    ids = {
        item.pattern_id
        for item in evaluate_evidence_patterns(candidate, observations, (), candidate_ids=("c1",))
    }
    assert {
        "reference_relative_rearrangement",
        "reference_relative_inversion",
        "repeated_reference_region",
        "missing_internal_reference_sequence",
    } <= ids


def test_reference_compatibility_vocabulary_is_loaded():
    from segpick.knowledge import describe_condition

    condition = describe_condition(
        "observation:unsupported_internal_candidate_region@reference_compatibility"
    )
    assert condition.display_name == "Internal candidate region lacks reference support"
    assert "closest reference" in condition.description


def test_evidence_pattern_evaluation_records_missing_support_and_conflict_state():
    from segpick.knowledge.schema import EvidencePatternDefinition
    from segpick.reasoning.rules import RuleCondition

    definition = EvidencePatternDefinition(
        pattern_id="test_pattern",
        title="Test pattern",
        category="test",
        scope="candidate",
        severity="review",
        base_confidence="moderate",
        interpretation="Test interpretation.",
        requires=(RuleCondition("observation", "required_signal"),),
        supports=(RuleCondition("observation", "optional_signal"),),
        conflicts=(RuleCondition("observation", "conflicting_signal"),),
    )
    observations = (
        EvidenceObservation("required_signal", ObservationSource.STRUCTURAL_ALIGNMENT, "required"),
        EvidenceObservation("conflicting_signal", ObservationSource.READ_COVERAGE, "conflict"),
    )

    evaluation = evaluate_evidence_patterns((definition,), observations, (), candidate_ids=("c1",))[0]

    assert evaluation.state == "contradicted"
    assert evaluation.matched_required == ("observation:required_signal",)
    assert evaluation.missing_supporting == ("observation:optional_signal",)
    assert evaluation.matched_conflicting == ("observation:conflicting_signal",)
    assert evaluation.confidence == "low"


def test_evidence_pattern_engine_still_omits_patterns_with_missing_requirements():
    from segpick.knowledge.schema import EvidencePatternDefinition
    from segpick.reasoning.rules import RuleCondition

    definition = EvidencePatternDefinition(
        pattern_id="incomplete_pattern",
        title="Incomplete pattern",
        category="test",
        scope="candidate",
        severity="review",
        base_confidence="moderate",
        interpretation="Test interpretation.",
        requires=(RuleCondition("observation", "required_signal"),),
    )

    assert evaluate_evidence_patterns((definition,), (), (), candidate_ids=("c1",)) == ()
