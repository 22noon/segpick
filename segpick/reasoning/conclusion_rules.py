from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from segpick.models import HypothesisEvaluation
from segpick.reasoning.rules import RuleCondition


@dataclass(frozen=True, slots=True)
class ConclusionCondition:
    """A condition on a biological hypothesis state."""

    target: str                    # hypothesis_id (e.g., "incomplete_segment")
    state: Literal["supported", "unsupported", "provisional", "contradicted", "any"]
    confidence: Literal["high", "moderate", "low", "provisional", "any"] = "any"
    role: Literal["required", "supporting", "conflicting"] = "required"
    kind: Literal["hypothesis"] = "hypothesis"

    def matches(self, hypothesis: HypothesisEvaluation | None) -> bool:
        """Check if the hypothesis satisfies this condition."""
        if hypothesis is None:
            return self.state == "any" or self.state == "unsupported"

        # Map hypothesis confidence to state categories
        hyp_confidence = hypothesis.confidence
        
        # Map confidence to state categories
        if self.state == "supported":
            if hyp_confidence not in ("high", "moderate"):
                return False
        elif self.state == "provisional":
            if hyp_confidence not in ("provisional", "moderate"):
                return False
        elif self.state == "unsupported":
            if hyp_confidence not in ("low", "provisional"):
                return False
        elif self.state == "contradicted":
            # HypothesisEvaluation doesn't have a "contradicted" state
            # Check if hypothesis is contradicted via its conflicting_patterns
            return bool(hypothesis.conflicting_patterns)
        elif self.state != "any":
            return False

        if self.confidence != "any" and hypothesis.confidence != self.confidence:
            return False

        return True


@dataclass(frozen=True, slots=True)
class HypothesisRelationship:
    """Explicit relationship between hypotheses that generates a conclusion."""

    type: Literal["jointly_supports", "competes_with"]
    targets: tuple[str, ...]  # hypothesis_ids (length >= 2)

    def satisfies(self, hypotheses: dict[str, object]) -> bool:
        """Check if the relationship is satisfied by the given hypotheses."""
        targets = [hypotheses.get(tid) for tid in self.targets]
        if any(h is None for h in targets):
            return False

        if self.type == "jointly_supports":
            return all(h.confidence in ("high", "moderate") for h in targets)
        elif self.type == "competes_with":
            # Competition is resolved if exactly one is supported (high/moderate) 
            # and the other is explicitly unsupported/contradicted.
            # If one is unresolved (provisional/low), competition is unresolved -> conditional.
            supported = [h.confidence in ("high", "moderate") for h in targets]
            unresolved = [h.confidence in ("provisional", "low") for h in targets]
            
            # Exactly one supported AND no unresolved = resolved competition
            if sum(supported) == 1 and not any(unresolved):
                return True
            # Any unresolved = competition unresolved
            if any(unresolved):
                return False
            # Both supported or both unsupported = not a clear competition
            return False

        return False


@dataclass(frozen=True, slots=True)
class ConclusionRule:
    """Declarative rule for creating a scientific conclusion from hypotheses."""

    rule_id: str
    title: str
    category: str
    scope: Literal["candidate", "gene"]
    severity: str
    base_confidence: Literal["low", "moderate", "high"]
    summary: str
    description: str = ""
    references: tuple[str, ...] = ()
    source: str = "builtin"

    # Atomic conditions on individual hypotheses
    conditions: tuple[object, ...] = ()  # ConclusionCondition objects

    # Explicit relationships among hypotheses
    relationships: tuple[object, ...] = ()  # HypothesisRelationship objects

    # Aggregate thresholds
    minimum_supported: int = 1
    minimum_confidence: Literal["low", "moderate", "high"] = "moderate"

    # Competing conclusions (mutually exclusive)
    contradicted_by: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()

    # Metadata
    source: str = "builtin"
    references: tuple[str, ...] = ()
    recommended_actions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScientificConclusionEvaluation:
    """Evaluation of a scientific conclusion for a specific candidate/gene."""

    conclusion_id: str
    title: str
    category: str
    scope: Literal["candidate", "gene"]
    state: Literal["supported", "conditional", "unsupported", "contradicted"]
    confidence: Literal["low", "moderate", "high", "provisional"]
    severity: str
    explanation: str
    base_confidence: str
    rule_id: str
    rule_version: str
    source: str
    references: tuple[str, ...]
    recommended_actions: tuple[str, ...]

    # Provenance
    supporting_hypotheses: tuple[str, ...]
    conflicting_hypotheses: tuple[str, ...]
    conditional_requirements: tuple[str, ...] = ()

    @property
    def is_supported(self) -> bool:
        return self.state == "supported"

    @property
    def is_conditional(self) -> bool:
        return self.state == "conditional"

    def to_dict(self) -> dict[str, object]:
        from dataclasses import asdict
        data = asdict(self)
        for key in ("supporting_hypotheses", "conflicting_hypotheses",
                    "conditional_requirements", "references", "recommended_actions"):
            data[key] = list(data[key])
        return data


def _eval_condition(cond, hypotheses: dict[str, object]) -> bool:
    """Evaluate a single condition against the hypothesis evaluations."""
    hyp = hypotheses.get(cond.target)
    return cond.matches(hyp)


def _eval_relationship(rel, hypotheses: dict[str, object]) -> bool:
    """Evaluate a hypothesis relationship."""
    return rel.satisfies(hypotheses)


def _is_genuine_conclusion(rule, hypotheses_by_id: dict) -> bool:
    """
    A conclusion must involve a relationship among at least two hypotheses.
    Prevent rules that merely turn one supported hypothesis into a conclusion.
    """
    if not rule.relationships:
        return False

    # Check that at least one relationship involves >= 2 hypotheses
    for rel in rule.relationships:
        if len(rel.targets) >= 2:
            return True
    return False


def _compute_conclusion_state(
    rule,
    hypotheses_by_id: dict,
    conditions_met: dict,
    rels_satisfied: dict,
) -> str:
    """Determine the state of a conclusion based on rule evaluation."""
    # Check required conditions - distinguish between "not met" (explicitly false) vs "unresolved"
    for cond in rule.conditions:
        if cond.role == "required":
            met = conditions_met.get(cond.target, False)
            if not met:
                # Check if the hypothesis exists but is unresolved (provisional/low)
                hyp = hypotheses_by_id.get(cond.target)
                if hyp is not None and hyp.confidence in ("provisional", "low"):
                    return "conditional"  # unresolved required hypothesis
                return "unsupported"  # explicitly unsupported or missing

    # Check conflicting conditions
    for cond in rule.conditions:
        if cond.role == "conflicting":
            met = conditions_met.get(cond.target, False)
            if met:
                return "contradicted"

    # Evaluate relationships - track if any required relationship is unresolved
    unresolved_relationship = False
    for rel in rule.relationships:
        if not rels_satisfied.get(rel.targets, False):
            if rel.type == "competes_with":
                return "conditional"  # competition unresolved
            elif rel.type == "jointly_supports":
                # Check if failure is due to unresolved hypothesis (conditional) vs unsupported
                targets = [hypotheses_by_id.get(tid) for tid in rel.targets]
                if any(h is not None and h.confidence in ("provisional", "low") for h in targets):
                    return "conditional"  # unresolved but not contradicted
            return "unsupported"

    # Count supported hypotheses from conditions
    supported_count = sum(
        1 for cond in rule.conditions
        if cond.role in ("required", "supporting")
        and conditions_met.get(cond.target, False)
    )

    if supported_count < rule.minimum_supported:
        return "unsupported"

    # Check for unresolved required hypotheses
    unresolved_required = any(
        cond.role == "required"
        and not conditions_met.get(cond.target, False)
        for cond in rule.conditions
    )

    if unresolved_required:
        return "conditional"

    return "supported"


def _build_conclusion_evaluation(rule, hypotheses_by_id: dict, state: str):
    """Build a ScientificConclusionEvaluation from a rule and hypothesis states."""
    # Collect supporting hypotheses
    supporting = []
    for cond in rule.conditions:
        if cond.role in ("required", "supporting") and cond.target in hypotheses_by_id:
            hyp = hypotheses_by_id[cond.target]
            if hyp.confidence in ("high", "moderate"):
                supporting.append(hyp.hypothesis_id)

    conflicting = []
    for cond in rule.conditions:
        if cond.role == "conflicting" and cond.target in hypotheses_by_id:
            hyp = hypotheses_by_id[cond.target]
            if hyp.confidence in ("high", "moderate"):
                conflicting.append(hyp.hypothesis_id)

    # Determine confidence based on rule base and hypothesis states
    confidence = rule.base_confidence
    if state == "conditional":
        confidence = "provisional"
    elif state == "contradicted":
        confidence = "low"

    # Collect conditional requirements
    conditional_reqs = []
    for cond in rule.conditions:
        if cond.role in ("required", "supporting"):
            # Check if this condition is NOT satisfied by creating a mock hypothesis
            class MockHyp:
                hypothesis_id = cond.target
                state = "supported"
                confidence = "high"
            mock_hyp = type('MockHyp', (), {
                'hypothesis_id': cond.target,
                'state': 'supported',
                'confidence': 'high',
            })()
            if not cond.matches(mock_hyp):
                conditional_reqs.append(cond.target)

    return ScientificConclusionEvaluation(
        conclusion_id=rule.rule_id,
        title=rule.title,
        category=rule.category,
        scope=rule.scope,
        state=state,
        confidence=confidence,
        severity=rule.severity,
        explanation=rule.description or rule.summary,
        base_confidence=rule.base_confidence,
        rule_id=rule.rule_id,
        rule_version="",
        source=rule.source,
        references=rule.references,
        recommended_actions=rule.recommended_actions,
        supporting_hypotheses=tuple(supporting),
        conflicting_hypotheses=tuple(conflicting),
        conditional_requirements=tuple(conditional_reqs),
    )


def evaluate_conclusions(
    rules: tuple[object, ...],
    hypotheses: tuple[object, ...],
    candidate_ids: tuple[str, ...] = (),
) -> tuple[object, ...]:
    """
    Evaluate conclusion rules against evaluated hypotheses.

    Args:
        rules: Tuple of ConclusionRule objects
        hypotheses: Tuple of HypothesisEvaluation objects
        candidate_ids: Candidate IDs for the evaluation

    Returns:
        Tuple of ScientificConclusionEvaluation objects
    """
    # Build hypothesis lookup by rule_id
    hypotheses_by_id = {h.hypothesis_id: h for h in hypotheses}

    results = []
    for rule in rules:
        # Skip if rule has no relationship (single-hypothesis rules not allowed)
        if not rule.relationships:
            continue

        # Evaluate atomic conditions
        conditions_met = {}
        for cond in rule.conditions:
            conditions_met[cond.target] = cond.matches(hypotheses_by_id.get(cond.target))

        # Evaluate relationships
        rels_satisfied = {}
        for rel in rule.relationships:
            rels_satisfied[rel.targets] = rel.satisfies({h.hypothesis_id: h for h in hypotheses})

        # Skip if not a valid conclusion (single hypothesis without relationship)
        if not _is_genuine_conclusion(rule, hypotheses_by_id):
            continue

        # Determine conclusion state
        state = _compute_conclusion_state(rule, hypotheses_by_id, conditions_met, rels_satisfied)

        # Build evaluation
        eval = _build_conclusion_evaluation(rule, hypotheses_by_id, state)
        results.append(eval)

    return tuple(results)


def load_active_conclusion_rules(
    user_rule_files: tuple[str, ...] = (),
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    """Load conclusion rules from builtin and user files."""
    from pathlib import Path

    builtin_path = Path(__file__).with_name("default_conclusion_rules.yml")
    if not builtin_path.exists():
        return (), ()

    raw = yaml.safe_load(builtin_path.read_text()) or {}
    if isinstance(raw, dict):
        rule_data = raw.get("rules", [])
    elif isinstance(raw, list):
        rule_data = raw
    else:
        rule_data = []

    rules = tuple(_parse_conclusion_rule(item) for item in rule_data)
    return split_conclusion_rules_by_scope(rules)


def _parse_conclusion_rule(raw: dict) -> object:
    """Parse a conclusion rule from YAML."""
    # Simplified for Phase 1
    return None


def split_conclusion_rules_by_scope(
    rules: tuple[object, ...]
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    candidate = tuple(r for r in rules if r.scope == "candidate")
    gene = tuple(r for r in rules if r.scope == "gene")
    return candidate, gene
