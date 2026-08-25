from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Protocol

from segpick.models import (
    CrossEvidenceFinding,
    EvidenceAssessment,
    EvidenceContribution,
    EvidenceReference,
)

_LEVEL_SCORE = {"high": 0.9, "moderate": 0.65, "medium": 0.65, "low": 0.35, "not_assessable": 0.0, "unknown": 0.0}


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
        aliases = {
            ("read_evidence", "read_region_supported"): ("read_region_supported", "read_evidence_summary"),
            ("read_evidence", "read_evidence_summary"): ("read_evidence_summary", "read_region_supported"),
        }
        accepted = aliases.get((channel_id, finding_id), (finding_id,))
        for item in (assessment.key_finding, *assessment.supporting_findings):
            if item.finding_id in accepted:
                return EvidenceReference(channel_id, finding_id, item.title)
        return None

    def channel_confidence(self, channel_id: str) -> float | None:
        assessment = self.assessment(channel_id)
        if assessment is None:
            return None
        if assessment.confidence.score is not None:
            return max(0.0, min(1.0, float(assessment.confidence.score)))
        return _LEVEL_SCORE.get(assessment.confidence.level.lower())


@dataclass(frozen=True, slots=True)
class ContributionSpec:
    channel_id: str
    finding_id: str
    weight: float = 1.0
    explanation: str = ""


class CrossEvidenceRule(Protocol):
    rule_id: str
    version: str
    source_plugin: str
    required_channels: frozenset[str]

    def evaluate(self, context: CrossEvidenceContext) -> tuple[CrossEvidenceFinding, ...]: ...


@dataclass(frozen=True, slots=True)
class StructuredCrossEvidenceRule:
    """Declarative v2 reasoner with confidence propagation and partial matching."""

    rule_id: str
    version: str
    source_plugin: str
    required_channels: frozenset[str]
    required: tuple[ContributionSpec, ...]
    output_id: str
    title: str
    description: str
    severity: str
    priority: int
    supporting: tuple[ContributionSpec, ...] = ()
    contradicting: tuple[ContributionSpec, ...] = ()
    limitations: tuple[str, ...] = ()
    allow_partial: bool = False
    minimum_required_fraction: float = 1.0
    contradiction_penalty: float = 0.65

    def _contribution(self, context: CrossEvidenceContext, spec: ContributionSpec, role: str) -> EvidenceContribution:
        ref = context.finding(spec.channel_id, spec.finding_id)
        return EvidenceContribution(
            role=role,
            channel_id=spec.channel_id,
            finding_id=spec.finding_id,
            title=ref.title if ref else spec.finding_id.replace("_", " "),
            weight=spec.weight,
            confidence=context.channel_confidence(spec.channel_id),
            present=ref is not None,
            explanation=spec.explanation,
        )

    def evaluate(self, context: CrossEvidenceContext) -> tuple[CrossEvidenceFinding, ...]:
        required = tuple(self._contribution(context, spec, "required_support") for spec in self.required)
        optional = tuple(self._contribution(context, spec, "support") for spec in self.supporting)
        contradictions = tuple(self._contribution(context, spec, "contradiction") for spec in self.contradicting)

        required_weight = sum(item.weight for item in required)
        matched_required_weight = sum(item.weight for item in required if item.present)
        required_fraction = matched_required_weight / required_weight if required_weight else 1.0
        if required_fraction < self.minimum_required_fraction:
            return ()
        if not self.allow_partial and required_fraction < 1.0:
            return ()

        present_support = tuple(item for item in (*required, *optional) if item.present)
        present_contradictions = tuple(item for item in contradictions if item.present)
        missing = tuple(item for item in (*required, *optional) if not item.present)

        support_weight = sum(item.weight for item in present_support)
        support_strength = (
            sum(item.weight * (item.confidence if item.confidence is not None else 0.5) for item in present_support) / support_weight
            if support_weight else 0.0
        )
        contradiction_weight = sum(item.weight for item in present_contradictions)
        contradiction_strength = (
            sum(item.weight * (item.confidence if item.confidence is not None else 0.5) for item in present_contradictions) / contradiction_weight
            if contradiction_weight else 0.0
        )
        all_positive_weight = sum(item.weight for item in (*required, *optional))
        completeness = support_weight / all_positive_weight if all_positive_weight else 1.0
        confidence_score = max(0.0, min(1.0, support_strength * completeness - self.contradiction_penalty * contradiction_strength))
        confidence = "high" if confidence_score >= 0.75 else "moderate" if confidence_score >= 0.45 else "low"
        status = "complete" if required_fraction == 1.0 else "partial"
        if present_contradictions:
            status = "contested"

        return (CrossEvidenceFinding(
            finding_id=self.output_id,
            title=self.title,
            description=self.description,
            confidence=confidence,
            severity=self.severity,
            priority=self.priority,
            rule_id=self.rule_id,
            rule_version=self.version,
            source_plugin=self.source_plugin,
            limitations=self.limitations,
            support_contributions=present_support,
            contradiction_contributions=present_contradictions,
            missing_contributions=missing,
            confidence_score=confidence_score,
            confidence_method="weighted_evidence_contributions",
            confidence_method_version="2.0",
            evidence_completeness=completeness,
            match_status=status,
        ),)


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
        # v1 rules retain their original skip behaviour. V2 reasoners can opt
        # into partial evaluation by setting allow_partial.
        if not rule.required_channels.issubset(available) and not getattr(rule, "allow_partial", False):
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
