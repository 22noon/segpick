from __future__ import annotations

from segpick.models import BiologicalScenario, ScenarioHypothesis

from .hypothesis_schema import HypothesisModule

_ORDER = ("low", "moderate", "high")


def evaluate_hypotheses(
    modules: tuple[HypothesisModule, ...],
    scenarios: tuple[BiologicalScenario, ...],
    candidate_ids: tuple[str, ...] = (),
) -> tuple[ScenarioHypothesis, ...]:
    scenario_by_id = {item.scenario_id: item for item in scenarios}
    results: list[ScenarioHypothesis] = []
    for module in modules:
        supporting = tuple(
            scenario_by_id[sid] for sid in module.supported_by if sid in scenario_by_id
        )
        if len(supporting) < module.minimum_support:
            continue
        conflicting = tuple(
            scenario_by_id[sid] for sid in module.contradicted_by if sid in scenario_by_id
        )
        confidence_index = _ORDER.index(module.base_confidence)
        if len(supporting) >= 2 and not conflicting:
            confidence_index = min(2, confidence_index + 1)
        if conflicting:
            confidence_index = max(0, confidence_index - 1)
        inferred_candidates = tuple(dict.fromkeys(
            candidate_id for scenario in supporting for candidate_id in scenario.candidate_ids
        ))
        results.append(ScenarioHypothesis(
            hypothesis_id=module.hypothesis_id,
            title=module.title,
            category=module.category,
            scope=module.scope,
            confidence=_ORDER[confidence_index],
            severity=module.severity,
            explanation=module.explanation,
            candidate_ids=candidate_ids or inferred_candidates,
            supporting_scenarios=tuple(item.scenario_id for item in supporting),
            supporting_scenario_titles=tuple(item.title for item in supporting),
            conflicting_scenarios=tuple(item.scenario_id for item in conflicting),
            conflicting_scenario_titles=tuple(item.title for item in conflicting),
            recommended_actions=module.recommended_actions,
            source=module.source,
            references=module.references,
        ))
    return tuple(results)
