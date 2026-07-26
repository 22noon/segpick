from __future__ import annotations

from segpick.models import BiologicalFinding, BiologicalHypothesis, EvidenceObservation

from .rules import HypothesisRule, RuleCondition

_CONFIDENCE_ORDER = ("low", "moderate", "high")


def _matched(
    conditions: tuple[RuleCondition, ...],
    observations: tuple[EvidenceObservation, ...],
    findings: tuple[BiologicalFinding, ...],
) -> tuple[str, ...]:
    return tuple(
        condition.label
        for condition in conditions
        if condition.matches(observations, findings)
    )


def _adjust_confidence(
    base: str,
    support_count: int,
    conflict_count: int,
) -> str:
    try:
        index = _CONFIDENCE_ORDER.index(base)
    except ValueError as exc:
        raise ValueError(f"Unsupported confidence level: {base}") from exc

    if support_count and not conflict_count:
        index += 1
    if conflict_count:
        index -= 1
    return _CONFIDENCE_ORDER[max(0, min(index, len(_CONFIDENCE_ORDER) - 1))]


def evaluate_rules(
    rules: tuple[HypothesisRule, ...],
    observations: tuple[EvidenceObservation, ...],
    findings: tuple[BiologicalFinding, ...],
    candidate_ids: tuple[str, ...] = (),
) -> tuple[BiologicalHypothesis, ...]:
    """Evaluate declarative rules and return traceable hypotheses."""

    hypotheses: list[BiologicalHypothesis] = []
    for rule in rules:
        required = _matched(rule.requires, observations, findings)
        if len(required) != len(rule.requires):
            continue

        supporting = _matched(rule.supports, observations, findings)
        conflicting = _matched(rule.conflicts, observations, findings)
        confidence = _adjust_confidence(
            rule.base_confidence,
            len(supporting),
            len(conflicting),
        )
        hypotheses.append(
            BiologicalHypothesis(
                rule_id=rule.rule_id,
                title=rule.title,
                category=rule.category,
                scope=rule.scope,
                confidence=confidence,
                severity=rule.severity,
                summary=rule.summary,
                candidate_ids=candidate_ids,
                matched_required=required,
                matched_supporting=supporting,
                matched_conflicting=conflicting,
            )
        )
    return tuple(hypotheses)
