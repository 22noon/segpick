"""
Query-time counterfactual reasoning for SegPick.

Given a reasoning graph node, virtually remove it and re-evaluate
affected evidence patterns and hypotheses using the existing
evaluation machinery. No graph mutation, no narrative generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from segpick.knowledge import (
    evaluate_evidence_patterns,
    evaluate_hypotheses,
    load_active_evidence_patterns,
    load_active_hypotheses,
)
from segpick.explorer import ReasoningExplorer
from segpick.models import (
    EvidenceObservation,
    BiologicalFinding,
    EvidencePatternEvaluation,
    HypothesisEvaluation,
)
from segpick.knowledge.schema import EvidencePatternDefinition
from segpick.knowledge.hypothesis_definition import HypothesisDefinition
from segpick.models.reasoning_graph import ReasoningGraph


@dataclass(frozen=True, slots=True)
class CounterfactualResult:
    """Result of a counterfactual evaluation."""
    removed_node_id: str
    removed_node_type: Literal["observation", "finding", "evidence_pattern"]
    
    # Before/after evaluations
    original_patterns: tuple[EvidencePatternEvaluation, ...]
    counterfactual_patterns: tuple[EvidencePatternEvaluation, ...]
    original_hypotheses: tuple[HypothesisEvaluation, ...]
    counterfactual_hypotheses: tuple[HypothesisEvaluation, ...]
    
    # Explicit deltas
    pattern_deltas: tuple["PatternDelta", ...]
    hypothesis_deltas: tuple["HypothesisDelta", ...]
    
    # Summary counts
    hypotheses_unchanged: int
    hypotheses_weakened: int
    hypotheses_no_longer_supported: int
    hypotheses_contradicted: int


@dataclass(frozen=True, slots=True)
class PatternDelta:
    pattern_id: str
    title: str
    original_state: str
    counterfactual_state: str
    change_type: Literal["unchanged", "weakened", "no_longer_matched", "now_contradicted"]
    lost_required_conditions: tuple[str, ...]
    lost_supporting_conditions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HypothesisDelta:
    hypothesis_id: str
    title: str
    original_confidence: str
    counterfactual_confidence: str
    original_state: str
    counterfactual_state: str
    change_type: Literal["unchanged", "weakened", "no_longer_supported", "contradicted"]
    lost_supporting_patterns: tuple[str, ...]
    gained_conflicting_patterns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _CounterfactualContext:
    """Internal context for counterfactual evaluation."""
    candidate_id: str
    observations: tuple[EvidenceObservation, ...]
    findings: tuple[BiologicalFinding, ...]
    evidence_patterns: tuple[EvidencePatternEvaluation, ...]
    biological_hypotheses: tuple[HypothesisEvaluation, ...]
    pattern_definitions: tuple[EvidencePatternDefinition, ...]
    hypothesis_definitions: tuple[HypothesisDefinition, ...]
    original_reasoning_graph: ReasoningGraph


def _filter_observation(obs: EvidenceObservation, node_id: str) -> bool:
    """Check if an observation matches the node_id to remove."""
    base = f"observation:{obs.source_name}:{obs.observation_type}"
    return node_id.startswith(base + ":")


def _filter_finding(finding: BiologicalFinding, node_id: str) -> bool:
    """Check if a finding matches the node_id to remove."""
    base = f"interpretation:{finding.title}:"
    return node_id.startswith(base)


def _filter_pattern(pattern: EvidencePatternEvaluation, node_id: str) -> bool:
    """Check if an evidence pattern matches the node_id to remove."""
    base = f"pattern:{pattern.pattern_id}:"
    return node_id.startswith(base)


def _build_counterfactual_context(
    candidate,
    pattern_definitions: tuple[EvidencePatternDefinition, ...],
    hypothesis_definitions: tuple[HypothesisDefinition, ...],
) -> _CounterfactualContext:
    """Extract all evaluation inputs from a candidate."""
    analysis = candidate.analysis
    
    return _CounterfactualContext(
        candidate_id=candidate.id,
        observations=analysis.observations,
        findings=analysis.findings,
        evidence_patterns=analysis.evidence_patterns,
        biological_hypotheses=analysis.biological_hypothesis_evaluations,
        pattern_definitions=pattern_definitions,
        hypothesis_definitions=hypothesis_definitions,
        original_reasoning_graph=analysis.reasoning_graph,
    )


def _remove_observation(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    """Virtually remove an observation from the evaluation context."""
    filtered_obs = tuple(o for o in context.observations if not _filter_observation(o, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=filtered_obs,
        findings=context.findings,
        evidence_patterns=context.evidence_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


def _remove_finding(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    """Virtually remove a finding from the evaluation context."""
    filtered_findings = tuple(f for f in context.findings if not _filter_finding(f, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=context.observations,
        findings=filtered_findings,
        evidence_patterns=context.evidence_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


def _remove_pattern(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    """Virtually remove an evidence pattern from the evaluation context."""
    filtered_patterns = tuple(p for p in context.evidence_patterns if not _filter_pattern(p, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=context.observations,
        findings=context.findings,
        evidence_patterns=filtered_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


def _evaluate_patterns(
    definitions: tuple[EvidencePatternDefinition, ...],
    observations: tuple[EvidenceObservation, ...],
    findings: tuple[BiologicalFinding, ...],
    candidate_ids: tuple[str, ...],
) -> tuple[EvidencePatternEvaluation, ...]:
    """Re-evaluate evidence patterns with modified inputs."""
    return evaluate_evidence_patterns(
        definitions,
        observations,
        findings,
        candidate_ids=candidate_ids,
        include_incomplete=True,
    )


def _evaluate_hypotheses(
    definitions: tuple[HypothesisDefinition, ...],
    patterns: tuple[EvidencePatternEvaluation, ...],
    candidate_ids: tuple[str, ...],
) -> tuple[HypothesisEvaluation, ...]:
    """Re-evaluate hypotheses with modified pattern inputs."""
    return evaluate_hypotheses(definitions, patterns, candidate_ids=candidate_ids)


def _compute_pattern_deltas(
    original: tuple[EvidencePatternEvaluation, ...],
    counterfactual: tuple[EvidencePatternEvaluation, ...],
) -> tuple["PatternDelta", ...]:
    """Compute deltas between original and counterfactual patterns."""
    original_by_id = {p.pattern_id: p for p in original}
    counterfactual_by_id = {p.pattern_id: p for p in counterfactual}
    all_ids = set(original_by_id.keys()) | set(counterfactual_by_id.keys())
    
    deltas = []
    for pid in sorted(all_ids):
        orig = original_by_id.get(pid)
        cf = counterfactual_by_id.get(pid)
        
        if orig and cf:
            orig_state = orig.state
            cf_state = cf.state
            
            if orig_state == cf_state:
                change_type = "unchanged"
            elif orig_state == "matched" and cf_state == "partially_matched":
                change_type = "weakened"
            elif orig_state in {"matched", "partially_matched"} and cf_state == "not_evaluable":
                change_type = "no_longer_matched"
            elif orig_state in {"matched", "partially_matched"} and cf_state == "contradicted":
                change_type = "now_contradicted"
            else:
                change_type = "unchanged"
            
            lost_required = tuple(c for c in orig.matched_required if c not in cf.matched_required)
            lost_supporting = tuple(c for c in orig.matched_supporting if c not in cf.matched_supporting)
            
        elif orig and not cf:
            change_type = "no_longer_matched"
            lost_required = orig.matched_required
            lost_supporting = orig.matched_supporting
        else:
            change_type = "unchanged"
            lost_required = ()
            lost_supporting = ()
        
        deltas.append(PatternDelta(
            pattern_id=pid,
            title=orig.title if orig else cf.title,
            original_state=orig.state if orig else "absent",
            counterfactual_state=cf.state if cf else "absent",
            change_type=change_type,
            lost_required_conditions=lost_required,
            lost_supporting_conditions=lost_supporting,
        ))
    
    return tuple(deltas)


def _compute_hypothesis_deltas(
    original: tuple[HypothesisEvaluation, ...],
    counterfactual: tuple[HypothesisEvaluation, ...],
) -> tuple["HypothesisDelta", ...]:
    """Compute deltas between original and counterfactual hypotheses."""
    original_by_id = {h.hypothesis_id: h for h in original}
    counterfactual_by_id = {h.hypothesis_id: h for h in counterfactual}
    all_ids = set(original_by_id.keys()) | set(counterfactual_by_id.keys())
    
    deltas = []
    for hid in sorted(all_ids):
        orig = original_by_id.get(hid)
        cf = counterfactual_by_id.get(hid)
        
        if orig and cf:
            orig_conf = orig.confidence
            cf_conf = cf.confidence
            
            if orig_conf == cf_conf:
                change_type = "unchanged"
            elif cf_conf in {"provisional", "low"} and orig_conf in {"moderate", "high"}:
                if cf_conf == "provisional":
                    change_type = "no_longer_supported"
                else:
                    change_type = "weakened"
            elif cf_conf == "contradicted" or getattr(cf, 'state', '') == "contradicted":
                change_type = "contradicted"
            else:
                change_type = "unchanged"
            
            lost_supporting = tuple(p for p in orig.supporting_patterns if p not in cf.supporting_patterns)
            gained_conflicting = tuple(p for p in cf.conflicting_patterns if p not in orig.conflicting_patterns)
            
        elif orig and not cf:
            change_type = "no_longer_supported"
            lost_supporting = orig.supporting_patterns
            gained_conflicting = ()
        else:
            change_type = "unchanged"
            lost_supporting = ()
            gained_conflicting = ()
        
        deltas.append(HypothesisDelta(
            hypothesis_id=hid,
            title=orig.title if orig else cf.title,
            original_confidence=orig.confidence if orig else "absent",
            counterfactual_confidence=cf.confidence if cf else "absent",
            original_state=getattr(orig, 'state', 'supported'),
            counterfactual_state=getattr(cf, 'state', 'supported'),
            change_type=change_type,
            lost_supporting_patterns=lost_supporting,
            gained_conflicting_patterns=gained_conflicting,
        ))
    
    return tuple(deltas)


def evaluate_counterfactual(
    candidate,
    node_id: str,
) -> CounterfactualResult:
    """
    Evaluate the counterfactual effect of removing a reasoning node.
    
    Args:
        candidate: CandidateContig with analysis data populated
        node_id: ID of the reasoning graph node to virtually remove
        
    Returns:
        CounterfactualResult with before/after evaluations and deltas
        
    Raises:
        KeyError: If node_id is not found in the reasoning graph
        ValueError: If the node type is not supported for counterfactual evaluation
    """
    # Load knowledge definitions once
    pattern_defs, _ = load_active_evidence_patterns()
    hypothesis_defs, _ = load_active_hypotheses()
    
    # Build context from candidate
    context = _build_counterfactual_context(candidate, pattern_defs, hypothesis_defs)
    
    # Determine node type first
    if node_id.startswith("observation:"):
        node_type = "observation"
    elif node_id.startswith("interpretation:"):
        node_type = "finding"
    elif node_id.startswith("pattern:"):
        node_type = "evidence_pattern"
    else:
        raise ValueError(f"Unsupported node type for counterfactual: {node_id}")
    
    # Check if node exists in graph
    all_node_ids = {
        n.id for n in context.original_reasoning_graph.observations
    } | {
        n.id for n in context.original_reasoning_graph.interpretive_findings
    } | {
        n.id for n in context.original_reasoning_graph.evidence_patterns
    }
    
    if node_id not in all_node_ids:
        raise KeyError(f"Unknown reasoning node '{node_id}'")
    
    # Create counterfactual context
    if node_type == "observation":
        cf_context = _remove_observation(context, node_id)
    elif node_type == "finding":
        cf_context = _remove_finding(context, node_id)
    elif node_type == "evidence_pattern":
        cf_context = _remove_pattern(context, node_id)
    else:
        raise ValueError(f"Unsupported node type for counterfactual: {node_type}")
    
    # Re-evaluate patterns
    new_patterns = _evaluate_patterns(
        cf_context.pattern_definitions,
        cf_context.observations,
        cf_context.findings,
        candidate_ids=(cf_context.candidate_id,),
    )
    
    # Re-evaluate hypotheses with new patterns
    new_hypotheses = _evaluate_hypotheses(
        cf_context.hypothesis_definitions,
        new_patterns,
        candidate_ids=(cf_context.candidate_id,),
    )
    
    # Compute deltas
    pattern_deltas = _compute_pattern_deltas(context.evidence_patterns, new_patterns)
    hypothesis_deltas = _compute_hypothesis_deltas(context.biological_hypotheses, new_hypotheses)
    
    # Summary counts
    unchanged = sum(1 for d in hypothesis_deltas if d.change_type == "unchanged")
    weakened = sum(1 for d in hypothesis_deltas if d.change_type == "weakened")
    no_longer_supported = sum(1 for d in hypothesis_deltas if d.change_type == "no_longer_supported")
    contradicted = sum(1 for d in hypothesis_deltas if d.change_type == "contradicted")
    
    return CounterfactualResult(
        removed_node_id=node_id,
        removed_node_type=node_type,
        original_patterns=context.evidence_patterns,
        counterfactual_patterns=new_patterns,
        original_hypotheses=context.biological_hypotheses,
        counterfactual_hypotheses=new_hypotheses,
        pattern_deltas=pattern_deltas,
        hypothesis_deltas=hypothesis_deltas,
        hypotheses_unchanged=unchanged,
        hypotheses_weakened=weakened,
        hypotheses_no_longer_supported=no_longer_supported,
        hypotheses_contradicted=contradicted,
    )


def _remove_observation(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    filtered_obs = tuple(o for o in context.observations if not _filter_observation(o, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=filtered_obs,
        findings=context.findings,
        evidence_patterns=context.evidence_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


def _remove_finding(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    filtered_findings = tuple(f for f in context.findings if not _filter_finding(f, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=context.observations,
        findings=filtered_findings,
        evidence_patterns=context.evidence_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


def _remove_pattern(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    filtered_patterns = tuple(p for p in context.evidence_patterns if not _filter_pattern(p, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=context.observations,
        findings=context.findings,
        evidence_patterns=filtered_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


@dataclass(frozen=True, slots=True)
class CounterfactualResult:
    """Result of a counterfactual evaluation."""
    removed_node_id: str
    removed_node_type: Literal["observation", "finding", "evidence_pattern"]
    
    # Before/after evaluations
    original_patterns: tuple[EvidencePatternEvaluation, ...]
    counterfactual_patterns: tuple[EvidencePatternEvaluation, ...]
    original_hypotheses: tuple[HypothesisEvaluation, ...]
    counterfactual_hypotheses: tuple[HypothesisEvaluation, ...]
    
    # Explicit deltas
    pattern_deltas: tuple[PatternDelta, ...]
    hypothesis_deltas: tuple[HypothesisDelta, ...]
    
    # Summary counts
    hypotheses_unchanged: int
    hypotheses_weakened: int
    hypotheses_no_longer_supported: int
    hypotheses_contradicted: int


@dataclass(frozen=True, slots=True)
class PatternDelta:
    pattern_id: str
    title: str
    original_state: str
    counterfactual_state: str
    change_type: Literal["unchanged", "weakened", "no_longer_matched", "now_contradicted"]
    lost_required_conditions: tuple[str, ...]
    lost_supporting_conditions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HypothesisDelta:
    hypothesis_id: str
    title: str
    original_confidence: str
    counterfactual_confidence: str
    original_state: str
    counterfactual_state: str
    change_type: Literal["unchanged", "weakened", "no_longer_supported", "contradicted"]
    lost_supporting_patterns: tuple[str, ...]
    gained_conflicting_patterns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _CounterfactualContext:
    """Internal context for counterfactual evaluation."""
    candidate_id: str
    observations: tuple[EvidenceObservation, ...]
    findings: tuple[BiologicalFinding, ...]
    evidence_patterns: tuple[EvidencePatternEvaluation, ...]
    biological_hypotheses: tuple[HypothesisEvaluation, ...]
    pattern_definitions: tuple[EvidencePatternDefinition, ...]
    hypothesis_definitions: tuple[HypothesisDefinition, ...]
    original_reasoning_graph: ReasoningGraph


from segpick.models.reasoning_graph import ReasoningGraph


def _remove_observation(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    filtered_obs = tuple(o for o in context.observations if not _filter_observation(o, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=filtered_obs,
        findings=context.findings,
        evidence_patterns=context.evidence_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


def _remove_finding(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    filtered_findings = tuple(f for f in context.findings if not _filter_finding(f, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=context.observations,
        findings=filtered_findings,
        evidence_patterns=context.evidence_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


def _remove_pattern(context: _CounterfactualContext, node_id: str) -> _CounterfactualContext:
    filtered_patterns = tuple(p for p in context.evidence_patterns if not _filter_pattern(p, node_id))
    return _CounterfactualContext(
        candidate_id=context.candidate_id,
        observations=context.observations,
        findings=context.findings,
        evidence_patterns=filtered_patterns,
        biological_hypotheses=context.biological_hypotheses,
        pattern_definitions=context.pattern_definitions,
        hypothesis_definitions=context.hypothesis_definitions,
        original_reasoning_graph=context.original_reasoning_graph,
    )


