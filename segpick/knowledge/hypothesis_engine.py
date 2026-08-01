from __future__ import annotations

from segpick.models import EvidencePatternEvaluation, HypothesisEvaluation

from .hypothesis_definition import HypothesisDefinition

_ORDER = ("low", "moderate", "high")


def evaluate_hypotheses(
    definitions: tuple[HypothesisDefinition, ...],
    patterns: tuple[EvidencePatternEvaluation, ...],
    candidate_ids: tuple[str, ...] = (),
) -> tuple[HypothesisEvaluation, ...]:
    pattern_by_id = {item.pattern_id: item for item in patterns}
    results: list[HypothesisEvaluation] = []
    for module in definitions:
        supporting = tuple(
            pattern_by_id[sid] for sid in module.supported_by if sid in pattern_by_id
        )
        if len(supporting) < module.minimum_support:
            continue
        conflicting = tuple(
            pattern_by_id[sid] for sid in module.contradicted_by if sid in pattern_by_id
        )
        confidence_index = _ORDER.index(module.base_confidence)
        if len(supporting) >= 2 and not conflicting:
            confidence_index = min(2, confidence_index + 1)
        if conflicting:
            confidence_index = max(0, confidence_index - 1)
        inferred_candidates = tuple(dict.fromkeys(
            candidate_id for pattern in supporting for candidate_id in pattern.candidate_ids
        ))
        results.append(HypothesisEvaluation(
            hypothesis_id=module.hypothesis_id,
            title=module.title,
            category=module.category,
            scope=module.scope,
            confidence=_ORDER[confidence_index],
            severity=module.severity,
            explanation=module.explanation,
            base_confidence=module.base_confidence,
            definition_supported_by=module.supported_by,
            definition_contradicted_by=module.contradicted_by,
            minimum_support=module.minimum_support,
            candidate_ids=candidate_ids or inferred_candidates,
            supporting_patterns=tuple(item.pattern_id for item in supporting),
            supporting_pattern_titles=tuple(item.title for item in supporting),
            conflicting_patterns=tuple(item.pattern_id for item in conflicting),
            conflicting_pattern_titles=tuple(item.title for item in conflicting),
            recommended_actions=module.recommended_actions,
            source=module.source,
            references=module.references,
        ))
    return tuple(results)
