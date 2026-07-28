from pathlib import Path

from segpick.cli import build_parser
from segpick.config import resolve_config
from segpick.knowledge import evaluate_scenarios, load_active_scenarios
from segpick.models import BiologicalFinding, EvidenceObservation, ObservationSource


def test_builtin_knowledge_modules_load_by_scope():
    candidate, gene = load_active_scenarios()
    assert any(item.scenario_id == "coverage_supported_assembly_breakpoint" for item in candidate)
    assert any(item.scenario_id == "complementary_fragmented_gene" for item in gene)


def test_scenario_evaluation_is_traceable_and_suggests_actions():
    candidate, _ = load_active_scenarios()
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
    scenarios = evaluate_scenarios(candidate, observations, (), candidate_ids=("c1",))
    scenario = next(item for item in scenarios if item.scenario_id == "coverage_supported_assembly_breakpoint")
    assert scenario.confidence == "high"
    assert scenario.candidate_ids == ("c1",)
    assert scenario.matched_required
    assert scenario.suggested_actions
    assert scenario.to_dict()["source"] == "builtin:default_scenarios.yml"


def test_user_knowledge_file_and_cli_override(tmp_path: Path):
    path = tmp_path / "knowledge.yml"
    path.write_text(
        """version: 1
scenarios:
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
    candidate, _ = load_active_scenarios((path,))
    assert any(item.scenario_id == "custom_case" and item.source == str(path) for item in candidate)

    args = build_parser().parse_args(["run", "--knowledge-file", str(path)])
    assert args.knowledge_files == [str(path)]
    config = resolve_config({}, {"knowledge_files": args.knowledge_files})
    assert config.knowledge_files == (path,)


def test_scenario_view_uses_human_friendly_observation_text():
    from segpick.models import BiologicalScenario
    from segpick.reporting.view_models import build_scenario_view

    scenario = BiologicalScenario(
        scenario_id="incomplete_terminal_assembly",
        title="Possible incomplete terminal assembly",
        category="completeness",
        scope="candidate",
        confidence="moderate",
        severity="review",
        interpretation="Possible truncation.",
        matched_required=("observation:weak_orf_terminal_support@read_coverage",),
    )
    view = build_scenario_view(scenario)
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


def test_scenario_provenance_records_measurements_regions_and_visualisations():
    candidate, _ = load_active_scenarios()
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
    scenario = next(
        item for item in evaluate_scenarios(candidate, observations, (), candidate_ids=("c1",))
        if item.scenario_id == "coverage_supported_assembly_breakpoint"
    )
    assert len(scenario.evidence_provenance) == 2
    structural = next(item for item in scenario.evidence_provenance if item.source == "structural_alignment")
    assert structural.descriptions == ("Two alignment blocks are separated by 318 nt.",)
    assert {item["name"] for item in structural.measurements} == {"gap_length", "hsp_count"}
    assert structural.regions[0]["start"] == 1201
    assert "reference_dotplot" in structural.visualisations
    payload = scenario.to_dict()
    assert payload["evidence_provenance"][0]["condition"].startswith("observation:")


def test_scenario_dashboard_uses_collapsed_nested_provenance(tmp_path):
    from segpick.reporting.html_report import write_html_dashboard
    from tests.test_recommendation_reporting import make_sample

    sample, recommendations = make_sample()
    candidate, _ = load_active_scenarios()
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
    contig.analysis.scenarios = evaluate_scenarios(candidate, contig.analysis.observations, (), candidate_ids=(contig.id,))
    write_html_dashboard(sample, tmp_path, recommendations)
    html = (tmp_path / "genes" / "VP2.html").read_text()
    assert '<details class="hypothesis-item scenario-item">' in html
    assert '<details class="provenance-item">' in html
    assert "Measurements" in html
    assert "Examine evidence" in html
    assert "observation:reference_structural_discontinuity" not in html
