from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import zipfile
from typing import Any

from segpick.models.reasoning_graph import ReasoningGraph


LLM_BUNDLE_VERSION = "1.0"

NODE_LAYER_ORDER = (
    "measurement",
    "observation",
    "interpretive_finding",
    "evidence_pattern",
    "biological_hypothesis",
)

EDGE_SEMANTICS = {
    "supported_by": "The source conclusion is supported by the target evidence.",
    "contradicted_by": "The source conclusion is challenged by the target evidence.",
    "derived_from": "The source finding was derived from the target observation.",
    "composed_from": "The source evidence pattern is composed from the target evidence.",
    "conflicted_by": "The source evidence pattern is challenged by the target evidence.",
}


def _measurement_summary(item: dict[str, Any]) -> str:
    unit = f" {item['unit']}" if item.get("unit") else ""
    return f"{item['name']} was measured as {item['value']}{unit}."


def _observation_summary(item: dict[str, Any]) -> str:
    description = str(item.get("description", "")).strip()
    return description if description.endswith((".", "!", "?")) else f"{description}."


def _finding_summary(item: dict[str, Any]) -> str:
    summary = str(item.get("summary", "")).strip()
    return summary if summary.endswith((".", "!", "?")) else f"{summary}."


def _pattern_summary(item: dict[str, Any]) -> str:
    interpretation = str(item.get("interpretation", "")).strip()
    return interpretation if interpretation.endswith((".", "!", "?")) else f"{interpretation}."


def _hypothesis_summary(item: dict[str, Any]) -> str:
    summary = str(item.get("summary", "")).strip()
    return summary if summary.endswith((".", "!", "?")) else f"{summary}."


_SUMMARY_BUILDERS = {
    "measurement": _measurement_summary,
    "observation": _observation_summary,
    "interpretive_finding": _finding_summary,
    "evidence_pattern": _pattern_summary,
    "biological_hypothesis": _hypothesis_summary,
}


def _normalised_nodes(graph: ReasoningGraph) -> list[dict[str, Any]]:
    groups = (
        ("measurement", graph.measurements),
        ("observation", graph.observations),
        ("interpretive_finding", graph.interpretive_findings),
        ("evidence_pattern", graph.evidence_patterns),
        ("biological_hypothesis", graph.biological_hypotheses),
    )
    nodes: list[dict[str, Any]] = []
    for node_type, items in groups:
        for item in items:
            payload = item.to_dict()
            nodes.append(
                {
                    "node_id": item.id,
                    "node_type": node_type,
                    "summary": _SUMMARY_BUILDERS[node_type](payload),
                    "data": payload,
                }
            )
    return nodes


def build_llm_reasoning_bundle(
    graph: ReasoningGraph,
    *,
    candidate_id: str,
    gene: str | None = None,
    segment: str | None = None,
    open_questions: tuple[str, ...] = (),
    measurement_only_components_omitted: int = 0,
) -> dict[str, Any]:
    """Create a self-describing, deterministic bundle for LLM review.

    The bundle does not ask an LLM to infer graph semantics. It includes layer
    order, edge meaning, uncertainty policy, node summaries, and authoritative
    node IDs so proposed conclusions can cite the graph precisely.
    """

    graph.validate()
    return {
        "bundle_version": LLM_BUNDLE_VERSION,
        "task_context": {
            "domain": "segmented viral genome assembly",
            "candidate_id": candidate_id,
            "gene": gene,
            "segment": segment,
        },
        "reasoning_model": {
            "layer_order": list(NODE_LAYER_ORDER),
            "edge_direction": "explanatory",
            "edge_semantics": EDGE_SEMANTICS,
            "missing_evidence_policy": "Missing evidence is not contradictory evidence.",
            "authority_policy": (
                "Graph nodes and edges are authoritative SegPick results. "
                "Any additional LLM conclusions must be labelled speculative."
            ),
        },
        "graph": {
            "nodes": _normalised_nodes(graph),
            "edges": [edge.to_dict() for edge in graph.edges],
        },
        "open_questions": list(open_questions),
        "pruning_summary": {
            "measurement_only_components_omitted": measurement_only_components_omitted,
        },
    }


def write_llm_reasoning_bundle(
    graph: ReasoningGraph,
    path: str | Path,
    **context: Any,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bundle = build_llm_reasoning_bundle(graph, **context)
    path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return path


def load_llm_bundle_schema() -> dict[str, Any]:
    schema_path = Path(__file__).with_name("llm_reasoning_bundle.schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_llm_output_schema() -> dict[str, Any]:
    schema_path = Path(__file__).with_name("llm_output.schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def build_llm_review_package(
    graph: ReasoningGraph,
    *,
    candidate_id: str,
    gene: str | None = None,
    segment: str | None = None,
    open_questions: tuple[str, ...] = (),
    measurement_only_components_omitted: int = 0,
) -> bytes:
    """Build a self-contained ZIP package for manual LLM review."""

    bundle = build_llm_reasoning_bundle(
        graph,
        candidate_id=candidate_id,
        gene=gene,
        segment=segment,
        open_questions=open_questions,
        measurement_only_components_omitted=measurement_only_components_omitted,
    )
    instructions = (
        "# SegPick LLM Review Package\n\n"
        "Review `reasoning_bundle.json` as a candidate-specific SegPick reasoning record.\n\n"
        "- Treat graph nodes and edges as authoritative SegPick results.\n"
        "- Distinguish missing evidence from contradictory evidence.\n"
        "- Label all new biological conclusions as speculative.\n"
        "- Cite supporting and conflicting graph node IDs.\n"
        "- Use `llm_output.schema.json` when structured output is supported.\n"
    )
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("reasoning_bundle.json", json.dumps(bundle, indent=2, sort_keys=True))
        zf.writestr(
            "llm_reasoning_bundle.schema.json",
            json.dumps(load_llm_bundle_schema(), indent=2, sort_keys=True),
        )
        zf.writestr(
            "llm_output.schema.json",
            json.dumps(load_llm_output_schema(), indent=2, sort_keys=True),
        )
        zf.writestr("README.md", instructions)
    return archive.getvalue()
