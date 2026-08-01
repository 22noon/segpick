import json

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from segpick.models import (
    InterpretiveFindingNode,
    ObservationNode,
    ReasoningEdge,
    ReasoningGraph,
)
from segpick.models.contig import CandidateContig
from segpick.models.metadata import ContigMetadata
from segpick.reporting.view_models import build_reasoning_graph_inspector_view


def _graph() -> ReasoningGraph:
    return ReasoningGraph(
        observations=(
            ObservationNode(
                id="observation:truncation:1",
                observation_type="protein_truncation",
                source="protein_alignment",
                description="N-terminal truncation observed.",
            ),
        ),
        interpretive_findings=(
            InterpretiveFindingNode(
                id="interpretive-finding:protein-truncation:1",
                title="Protein truncation detected",
                summary="Protein alignment evidence is consistent with truncation.",
            ),
        ),
        edges=(
            ReasoningEdge(
                source_id="interpretive-finding:protein-truncation:1",
                target_id="observation:truncation:1",
                relationship="derived_from",
            ),
        ),
    )


def test_normalized_graph_has_single_node_and_edge_collections():
    payload = _graph().to_normalized_dict()

    assert payload["format"] == "segpick-normalized-reasoning-graph"
    assert {node["type"] for node in payload["nodes"]} == {
        "observation",
        "interpretive_finding",
    }
    assert payload["edges"] == [
        {
            "source": "interpretive-finding:protein-truncation:1",
            "target": "observation:truncation:1",
            "relationship": "derived_from",
            "label": "derived from",
        }
    ]
    assert payload["component_summary"]["classification_counts"] == {
        "unresolved_interpretive_finding": 1
    }
    assert "interpretive_findings" not in payload
    assert "observations" not in payload


def test_inspector_exposes_normalized_graph_json():
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(Seq("ATGC"), id="contig_a"),
        metadata=ContigMetadata(segment="1", score=1.0, confidence=1.0, cluster="test"),
    )
    candidate.analysis.reasoning_graph = _graph()

    view = build_reasoning_graph_inspector_view(candidate)
    payload = json.loads(view.normalized_graph_json)

    assert payload["nodes"][0]["type"] in {"observation", "interpretive_finding"}
    assert payload["edges"][0]["relationship"] == "derived_from"


def test_dashboard_exposes_normalized_graph_download():
    from pathlib import Path

    template = Path("segpick/reporting/templates/gene.html").read_text(encoding="utf-8")
    assert "Download normalized graph JSON" in template
    assert "data-normalized-graph-candidate" in template
    assert "normalized_reasoning_graph.json" in template


def test_reasoning_components_classify_highest_reached_layer():
    graph = _graph()
    components = graph.reasoning_components()

    assert len(components) == 1
    component = components[0]
    assert component.highest_level == "interpretive_finding"
    assert component.classification == "unresolved_interpretive_finding"
    assert component.next_level == "evidence_pattern"
    assert component.node_count == 2
    assert component.edge_count == 1


def test_measurement_only_component_is_reported_separately():
    from segpick.models import MeasurementNode

    graph = ReasoningGraph(
        measurements=(MeasurementNode(id="measurement:depth:1", channel="coverage", name="Depth", value=10),)
    )
    summary = graph.component_summary()

    assert summary["measurement_only_components"] == 1
    assert summary["components"][0]["highest_level"] == "measurement"


def test_inspector_exposes_reasoning_component_summary():
    candidate = CandidateContig(
        id="contig_a",
        record=SeqRecord(Seq("ATGC"), id="contig_a"),
        metadata=ContigMetadata(segment="1", score=1.0, confidence=1.0, cluster="test"),
    )
    candidate.analysis.reasoning_graph = _graph()

    view = build_reasoning_graph_inspector_view(candidate)

    assert view.component_count == 1
    assert view.finding_component_count == 1
    assert view.components[0].next_level == "evidence_pattern"


def test_dashboard_exposes_reasoning_component_summary():
    from pathlib import Path

    template = Path("segpick/reporting/templates/gene.html").read_text(encoding="utf-8")
    assert "Reasoning component summary" in template
    assert "Reasoning completeness by component" in template
    assert "Measurement-only" in template
