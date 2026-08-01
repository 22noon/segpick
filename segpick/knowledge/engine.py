from __future__ import annotations

from typing import Any

from segpick.models import EvidencePatternEvaluation, EvidencePatternProvenance
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
        return EvidencePatternProvenance(
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
    return EvidencePatternProvenance(
        condition=condition.label,
        kind="finding",
        source=source,
        descriptions=tuple(dict.fromkeys(item.summary for item in matches if item.summary)),
        measurements=(),
        regions=(),
        visualisations=tuple(dict.fromkeys(v for src in sources for v in _visualisations(src))),
    )


def evaluate_scenarios(modules, observations, findings, candidate_ids=(), include_incomplete=False):
    out = []
    for module in modules:
        required_conditions = tuple(c for c in module.requires if c.matches(observations, findings))
        missing_required = tuple(c for c in module.requires if c not in required_conditions)
        if missing_required and not include_incomplete:
            continue

        supporting_conditions = tuple(c for c in module.supports if c.matches(observations, findings))
        missing_supporting = tuple(c for c in module.supports if c not in supporting_conditions)
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

        referenced_finding_titles = {
            condition.value
            for condition in module.requires + module.supports + module.conflicts
            if condition.kind == "finding"
        }
        unused_findings = tuple(dict.fromkeys(
            item.title for item in findings
            if item.title not in referenced_finding_titles
        ))

        out.append(EvidencePatternEvaluation(
            scenario_id=module.scenario_id,
            title=module.title,
            category=module.category,
            scope=module.scope,
            confidence=_ORDER[confidence_index],
            severity=module.severity,
            interpretation=module.interpretation,
            candidate_ids=candidate_ids,
            matched_required=tuple(c.label for c in required_conditions),
            matched_supporting=tuple(c.label for c in supporting_conditions),
            matched_conflicting=tuple(c.label for c in conflicting_conditions),
            suggested_actions=module.suggested_actions,
            source=module.source,
            references=module.references,
            evidence_provenance=provenance,
            state=(
                "not_evaluable" if len(missing_required) == len(module.requires) and not supporting_conditions and not conflicting_conditions
                else "partially_matched" if missing_required
                else "contradicted" if conflicting_conditions
                else "matched"
            ),
            missing_required=tuple(c.label for c in missing_required),
            missing_supporting=tuple(c.label for c in missing_supporting),
            unused_findings=unused_findings,
        ))
    return tuple(out)
