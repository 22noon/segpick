from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Protocol

from segpick.models import CrossEvidenceFinding, EvidenceAssessment, EvidenceReference


@dataclass(frozen=True, slots=True)
class CrossEvidenceContext:
    assessments: tuple[EvidenceAssessment, ...]
    candidate_id: str
    gene: str

    def assessment(self, channel_id: str) -> EvidenceAssessment | None:
        return next((item for item in self.assessments if item.channel_id == channel_id), None)

    def finding(self, channel_id: str, finding_id: str) -> EvidenceReference | None:
        assessment = self.assessment(channel_id)
        if assessment is None:
            return None
        for item in (assessment.key_finding, *assessment.supporting_findings):
            if item.finding_id == finding_id:
                return EvidenceReference(channel_id, finding_id, item.title)
        return None


class CrossEvidenceRule(Protocol):
    rule_id: str
    version: str
    source_plugin: str
    required_channels: frozenset[str]

    def evaluate(self, context: CrossEvidenceContext) -> tuple[CrossEvidenceFinding, ...]: ...


RULE_REGISTRY: dict[str, CrossEvidenceRule] = {}


def register_rule(rule: CrossEvidenceRule) -> CrossEvidenceRule:
    if rule.rule_id in RULE_REGISTRY:
        raise ValueError(f"Cross-evidence rule already registered: {rule.rule_id}")
    RULE_REGISTRY[rule.rule_id] = rule
    return rule


def evaluate_cross_evidence(context: CrossEvidenceContext) -> tuple[CrossEvidenceFinding, ...]:
    available = {item.channel_id for item in context.assessments}
    results: list[CrossEvidenceFinding] = []
    for rule in RULE_REGISTRY.values():
        if not rule.required_channels.issubset(available):
            continue
        results.extend(rule.evaluate(context))
    return tuple(sorted(results, key=lambda item: item.priority, reverse=True))


def discover_external_rules(group: str = "segpick.cross_evidence_rules") -> tuple[str, ...]:
    loaded: list[str] = []
    for entry_point in entry_points().select(group=group):
        obj = entry_point.load()
        rules = obj() if callable(obj) and not hasattr(obj, "evaluate") else obj
        if not isinstance(rules, (tuple, list)):
            rules = (rules,)
        for rule in rules:
            register_rule(rule)
            loaded.append(rule.rule_id)
    return tuple(loaded)
