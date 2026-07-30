from __future__ import annotations

from typing import Any

from segpick.models import BiologicalScenario, ScenarioEvidenceProvenance
from .schema import KnowledgeModule

_ORDER = ("low", "moderate", "high")


def _measurement_items(attributes: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {"name": str(name), "value": value}
        for name, value in sorted(attributes.items())
        if isinstance(value, (str, int, float, bool)) or value is None
    )


def _visualisations(source: str | None) -> tuple[str, ...]:
    mapping = {
        "read_coverage": ("coverage_plot",),
        "cross_evidence": ("coverage_plot", "reference_dotplot"),
        "structural_alignment": ("reference_dotplot",),
        "reference_compatibility": ("reference_dotplot", "coverage_plot"),
        "protein_alignment": ("protein_alignment",),
        "orf_structure": ("orf_summary", "coverage_plot"),
        "protein_continuity": ("protein_continuity",),
        "diamond": ("protein_similarity",),
    }
    return mapping.get(source, ())


def _condition_provenance(condition, observations, findings):
    if condition.kind == "observation":
        matches = tuple(
            item for item in observations
            if item.observation_type == condition.value
            and (condition.source is None or item.source_name == condition.source)
        )
        measurements = []
        regions = []
        for item in matches:
            measurements.extend(_measurement_items(item.attributes))
            if item.is_spatial:
                regions.append({
                    "coordinate_system": item.coordinate_system,
                    "start": item.start,
                    "end": item.end,
                    "length": item.length,
                })
        source = condition.source or (matches[0].source_name if matches else None)
        return ScenarioEvidenceProvenance(
            condition=condition.label,
            kind="observation",
            source=source,
            descriptions=tuple(dict.fromkeys(item.description for item in matches if item.description)),
            measurements=tuple(measurements),
            regions=tuple(regions),
            visualisations=_visualisations(source),
        )

    matches = tuple(
        item for item in findings
        if item.title == condition.value
        and (condition.source is None or condition.source in item.sources)
    )
    sources = tuple(dict.fromkeys(source for item in matches for source in item.sources))
    source = condition.source or (sources[0] if len(sources) == 1 else None)
    return ScenarioEvidenceProvenance(
        condition=condition.label,
        kind="finding",
        source=source,
        descriptions=tuple(dict.fromkeys(item.summary for item in matches if item.summary)),
        measurements=(),
        regions=(),
        visualisations=tuple(dict.fromkeys(v for src in sources for v in _visualisations(src))),
    )


def evaluate_scenarios(modules, observations, findings, candidate_ids=()):
    out = []
    for module in modules:
        required_conditions = tuple(c for c in module.requires if c.matches(observations, findings))
        if len(required_conditions) != len(module.requires):
            continue
        supporting_conditions = tuple(c for c in module.supports if c.matches(observations, findings))
        conflicting_conditions = tuple(c for c in module.conflicts if c.matches(observations, findings))
        confidence_index = _ORDER.index(module.base_confidence)
        if supporting_conditions and not conflicting_conditions:
            confidence_index = min(2, confidence_index + 1)
        if conflicting_conditions:
            confidence_index = max(0, confidence_index - 1)
        matched = required_conditions + supporting_conditions + conflicting_conditions
        provenance = tuple(
            _condition_provenance(condition, observations, findings)
            for condition in matched
        )
        out.append(BiologicalScenario(
            module.scenario_id,
            module.title,
            module.category,
            module.scope,
            _ORDER[confidence_index],
            module.severity,
            module.interpretation,
            candidate_ids,
            tuple(c.label for c in required_conditions),
            tuple(c.label for c in supporting_conditions),
            tuple(c.label for c in conflicting_conditions),
            module.suggested_actions,
            module.source,
            module.references,
            provenance,
        ))
    return tuple(out)
