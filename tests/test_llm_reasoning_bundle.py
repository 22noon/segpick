from io import BytesIO
import json
import zipfile

import jsonschema

from segpick.models import (
    BiologicalHypothesisNode,
    EvidencePatternNode,
    InterpretiveFindingNode,
    MeasurementNode,
    ObservationNode,
    ReasoningEdge,
    ReasoningGraph,
)
from segpick.reasoning import (
    build_llm_reasoning_bundle,
    build_llm_review_package,
    load_llm_bundle_schema,
    load_llm_output_schema,
    write_llm_reasoning_bundle,
)


def _graph() -> ReasoningGraph:
    measurement = MeasurementNode(
        id="measurement:blocks:1",
        channel="structural_alignment",
        name="Alignment block count",
        value=4,
        unit="blocks",
    )
    observation = ObservationNode(
        id="observation:fragmented:1",
        observation_type="fragmented_alignment",
        source="structural_alignment",
        description="Several separated alignment blocks are present",
    )
    finding = InterpretiveFindingNode(
        id="finding:fragmentation:1",
        title="Fragmentation is plausible",
        summary="The alignment structure is consistent with fragmentation",
    )
    pattern = EvidencePatternNode(
        id="pattern:partial:1",
        pattern_id="partial_assembly_pattern",
        title="Partial assembly evidence pattern",
        interpretation="Fragmentation and incomplete continuity form a partial assembly pattern",
        confidence="moderate",
    )
    hypothesis = BiologicalHypothesisNode(
        id="hypothesis:partial:1",
        title="Partial assembly",
        summary="The candidate is most consistent with a partial assembly",
        confidence="moderate",
    )
    graph = ReasoningGraph(
        measurements=(measurement,),
        observations=(observation,),
        interpretive_findings=(finding,),
        evidence_patterns=(pattern,),
        biological_hypotheses=(hypothesis,),
        edges=(
            ReasoningEdge(observation.id, measurement.id, "supported_by"),
            ReasoningEdge(finding.id, observation.id, "derived_from"),
            ReasoningEdge(pattern.id, finding.id, "composed_from"),
            ReasoningEdge(hypothesis.id, pattern.id, "supported_by"),
        ),
    )
    graph.validate()
    return graph


def test_llm_bundle_is_self_describing_and_schema_valid():
    bundle = build_llm_reasoning_bundle(
        _graph(),
        candidate_id="contig_a",
        gene="VP2",
        segment="2",
        open_questions=("Is breakpoint read support available?",),
        measurement_only_components_omitted=3,
    )

    jsonschema.validate(bundle, load_llm_bundle_schema())
    assert bundle["reasoning_model"]["edge_direction"] == "explanatory"
    assert "Missing evidence is not contradictory" in bundle["reasoning_model"]["missing_evidence_policy"]
    assert bundle["pruning_summary"]["measurement_only_components_omitted"] == 3
    assert [node["node_type"] for node in bundle["graph"]["nodes"]] == [
        "measurement",
        "observation",
        "interpretive_finding",
        "evidence_pattern",
        "biological_hypothesis",
    ]
    assert all(node["summary"].endswith(".") for node in bundle["graph"]["nodes"])


def test_llm_bundle_writer_outputs_json(tmp_path):
    path = write_llm_reasoning_bundle(
        _graph(),
        tmp_path / "contig_a.llm.json",
        candidate_id="contig_a",
    )
    payload = json.loads(path.read_text())
    jsonschema.validate(payload, load_llm_bundle_schema())
    assert payload["task_context"]["candidate_id"] == "contig_a"


def test_llm_output_schema_requires_speculative_hypotheses():
    output = {
        "graph_supported_summary": "The graph supports a partial assembly interpretation.",
        "alternative_hypotheses": [
            {
                "title": "Assembler graph collapse",
                "rationale": "Fragmentation may reflect collapsed repeat resolution.",
                "supporting_node_ids": ["finding:fragmentation:1"],
                "conflicting_node_ids": [],
                "status": "speculative",
            }
        ],
        "evidence_gaps": [],
        "warnings": [],
    }
    jsonschema.validate(output, load_llm_output_schema())


def test_llm_review_package_contains_bundle_schemas_and_instructions():
    payload = build_llm_review_package(
        _graph(),
        candidate_id="contig_a",
        gene="VP2",
        segment="2",
    )
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        assert set(archive.namelist()) == {
            "reasoning_bundle.json",
            "llm_reasoning_bundle.schema.json",
            "llm_output.schema.json",
            "README.md",
        }
        bundle = json.loads(archive.read("reasoning_bundle.json"))
        jsonschema.validate(bundle, json.loads(archive.read("llm_reasoning_bundle.schema.json")))
        instructions = archive.read("README.md").decode("utf-8")
        assert "Label all new biological conclusions as speculative" in instructions
