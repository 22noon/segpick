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
