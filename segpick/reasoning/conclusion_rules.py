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
    
    # Generating relationship provenance
    generating_relationship: str = ""  # "jointly_supports" or "competes_with"
    generating_hypotheses: tuple[str, ...] = ()  # hypothesis IDs involved in the relationship

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

    # Evaluate relationships first - track if any required relationship is unresolved
    # For competes_with, relationship evaluation takes precedence over conflicting conditions
    # per frozen design: two competing hypotheses both supported = unsupported (not contradicted)
    for rel in rule.relationships:
        if not rels_satisfied.get(rel.targets, False):
            if rel.type == "competes_with":
                # Check if competition is actually unresolved (one supported, one provisional/low)
                # If both supported or both unsupported -> unsupported (not conditional)
                targets = [hypotheses_by_id.get(tid) for tid in rel.targets]
                supported = [h is not None and h.confidence in ("high", "moderate") for h in targets]
                unresolved = [h is not None and h.confidence in ("provisional", "low") for h in targets]
                
                # Exactly one supported AND no unresolved = resolved competition (relationship satisfied, won't be here)
                # Any unresolved = competition unresolved -> conditional
                if any(unresolved):
                    return "conditional"
                # Both supported or both unsupported = not a clear competition -> unsupported
                return "unsupported"
            elif rel.type == "jointly_supports":
                # Check if failure is due to unresolved hypothesis (conditional) vs unsupported
                targets = [hypotheses_by_id.get(tid) for tid in rel.targets]
                if any(h is not None and h.confidence in ("provisional", "low") for h in targets):
                    return "conditional"  # unresolved but not contradicted
            return "unsupported"

    # Check conflicting conditions - but only if not part of a competes_with relationship
    for cond in rule.conditions:
        if cond.role == "conflicting":
            # Check if this hypothesis is part of a competes_with relationship
            in_competes_with = any(
                cond.target in rel.targets and rel.type == "competes_with"
                for rel in rule.relationships
            )
            if in_competes_with:
                # For competing hypotheses, don't auto-contradict; relationship handles it
                continue
            met = conditions_met.get(cond.target, False)
            if met:
                return "contradicted"

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

    # Determine generating relationship
    generating_rel = ""
    generating_hyps = ()
    for rel in rule.relationships:
        if len(rel.targets) >= 2:
            generating_rel = rel.type
            generating_hyps = rel.targets
            break

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
        generating_relationship=generating_rel,
        generating_hypotheses=generating_hyps,
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


def _parse_conclusion_rule(raw: dict) -> ConclusionRule:
    """Parse a conclusion rule from YAML."""

    if not isinstance(raw, dict):
        raise ValueError(f"Rule must be a mapping, got {type(raw)}")

    unknown = set(raw) - {
        "id", "title", "description", "category", "scope", "severity",
        "base_confidence", "summary", "conditions", "relationships",
        "minimum_supported", "minimum_confidence", "contradicted_by", "contradicts",
        "references", "source", "recommended_actions",
    }
    if unknown:
        raise ValueError(f"Unknown rule fields: {sorted(unknown)}")

    rule_id = raw.get("id")
    if not rule_id:
        raise ValueError("Rule must have an 'id'")

    scope = raw.get("scope", "candidate")
    if scope not in ("candidate", "gene"):
        raise ValueError(f"Invalid scope '{scope}'")

    confidence = raw.get("base_confidence", "moderate")
    if confidence not in ("low", "moderate", "high"):
        raise ValueError(f"Invalid base_confidence '{confidence}'")

    severity = raw.get("severity", "review")
    if severity not in ("informational", "review", "warning"):
        raise ValueError(f"Invalid severity '{severity}'")

    # Parse conditions
    conditions = []
    for raw_cond in raw.get("conditions", ()):
        cond = _parse_conclusion_condition(raw_cond)
        conditions.append(cond)

    # Parse relationships
    relationships = []
    for raw_rel in raw.get("relationships", ()):
        rel = _parse_hypothesis_relationship(raw_rel)
        relationships.append(rel)

    # Parse contradicted_by / contradicts
    contradicted_by = tuple(raw.get("contradicted_by", ()))
    contradicts = tuple(raw.get("contradicts", ()))

    return ConclusionRule(
        rule_id=rule_id,
        title=raw.get("title", ""),
        category=raw.get("category", ""),
        scope=scope,
        severity=severity,
        base_confidence=confidence,
        summary=raw.get("summary", ""),
        description=raw.get("description", ""),
        references=tuple(raw.get("references", ())),
        source=raw.get("source", "builtin"),
        conditions=tuple(conditions),
        relationships=tuple(relationships),
        minimum_supported=raw.get("minimum_supported", 1),
        contradicted_by=contradicted_by,
        contradicts=contradicts,
        recommended_actions=tuple(raw.get("recommended_actions", ())),
    )


def _parse_conclusion_condition(raw: dict) -> ConclusionCondition:
    """Parse a single conclusion condition from YAML."""
    if not isinstance(raw, dict):
        raise ValueError(f"Condition must be a mapping, got {type(raw)}")
    
    target = raw.get("target")
    if not target or not isinstance(target, str):
        raise ValueError("Condition must have a 'target' string field")
    
    state = raw.get("state", "any")
    if state not in ("supported", "unsupported", "provisional", "contradicted", "any"):
        raise ValueError(f"Invalid state '{state}'")
    
    confidence = raw.get("confidence", "any")
    if confidence not in ("high", "moderate", "low", "provisional", "any"):
        raise ValueError(f"Invalid confidence '{confidence}'")
    
    role = raw.get("role", "required")
    if role not in ("required", "supporting", "conflicting"):
        raise ValueError(f"Invalid role '{role}'")
    
    return ConclusionCondition(
        target=target.strip(),
        state=state,
        confidence=confidence,
        role=role,
    )


def _parse_hypothesis_relationship(raw: dict) -> HypothesisRelationship:
    """Parse a hypothesis relationship from YAML."""
    if not isinstance(raw, dict):
        raise ValueError(f"Relationship must be a mapping, got {type(raw)}")
    
    rel_type = raw.get("type")
    if not rel_type or rel_type not in ("jointly_supports", "competes_with"):
        raise ValueError("Relationship must have type 'jointly_supports' or 'competes_with'")
    
    targets = raw.get("targets")
    if not targets or not isinstance(targets, (list, tuple)) or len(targets) < 2:
        raise ValueError("Relationship must have 'targets' list with at least 2 elements")
    
    return HypothesisRelationship(
        type=rel_type,
        targets=tuple(str(t).strip() for t in targets),
    )


def _parse_hypothesis_relationship(raw: dict) -> HypothesisRelationship:
    """Parse a hypothesis relationship from YAML."""
    if not isinstance(raw, dict):
        raise ValueError(f"Relationship must be a mapping, got {type(raw)}")
    
    rel_type = raw.get("type")
    if not rel_type or rel_type not in ("jointly_supports", "competes_with"):
        raise ValueError("Relationship must have type 'jointly_supports' or 'competes_with'")
    
    targets = raw.get("targets")
    if not targets or not isinstance(targets, (list, tuple)) or len(targets) < 2:
        raise ValueError("Relationship must have 'targets' list with at least 2 elements")
    
    return HypothesisRelationship(
        type=rel_type,
        targets=tuple(str(t).strip() for t in targets),
    )


def _parse_conditions(
    raw: list,
    source: str,
) -> tuple[RuleCondition, ...]:
    """Parse a list of conditions from YAML."""
    return tuple(_parse_conclusion_condition(raw_cond) for raw_cond in raw)


def _parse_relationships(
    raw: list,
    source: str,
) -> tuple[HypothesisRelationship, ...]:
    """Parse a list of relationships from YAML."""
    return tuple(_parse_hypothesis_relationship(raw) for raw in raw)




def split_conclusion_rules_by_scope(
    rules: tuple[object, ...]
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    candidate = tuple(r for r in rules if r.scope == "candidate")
    gene = tuple(r for r in rules if r.scope == "gene")
    return candidate, gene
