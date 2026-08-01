# SegPick Reasoning Model

## Purpose

SegPick is an explainable reasoning engine for evaluating competing biological explanations of assembled viral genome segments.

Every recommendation must be traceable back to the measurements from which it was derived.

The reasoning graph is an immutable provenance graph describing scientific reasoning rather than software execution.

---

# Design Principles

## Hierarchical abstraction

Measurement
→ Observation
→ Interpretive Finding
→ Evidence Pattern
→ Biological Hypothesis
→ Recommendation

Each layer answers one scientific question.

| Layer | Scientific question |
|--------|---------------------|
| Measurement | What was measured? |
| Observation | What was observed? |
| Interpretive Finding | What does this observation suggest? |
| Evidence Pattern | What overall pattern emerges? |
| Biological Hypothesis | What biological explanation best explains that pattern? |
| Recommendation | What action should be taken? |

## Evidence aggregation

Each reasoning object is created by evaluating one or more objects from the immediately preceding reasoning layer.

Objects + Knowledge = New reasoning object

Lower-level objects remain immutable and may contribute to multiple higher-level objects.

## Provenance

Every reasoning object must be traceable back to supporting measurements through explicit graph edges.

## Explicit uncertainty

Failure to construct a higher-level reasoning object is itself scientifically meaningful.

Reasoning terminates naturally at the highest justified layer.

## Immutable reasoning

Reasoning objects are never modified after creation.

---

# Reasoning Layers

## Measurement

Objective quantities produced by analytical plugins.

Produces: Observation

Examples:
- Alignment block count
- ORF length
- Mean read depth
- Coverage uniformity

## Observation

Observable properties derived from measurements.

Produces: Interpretive Finding

Examples:
- Repeated mapping observed
- Complete ORF observed
- Uniform coverage observed

## Interpretive Finding

Interpretation of one or more observations.

Produces: Evidence Pattern

Examples:
- Fragmentation is plausible
- Coding continuity is preserved
- Repeated sequence is plausible

## Evidence Pattern

Recognised combination of interpretive findings.

Question answered:

What overall pattern emerges from the available findings?

Produces: Biological Hypothesis

Examples:
- Repeated mapping with coding continuity
- Fragmentation pattern
- Genome integrity pattern

States:
- matched
- partially matched
- contradicted
- not evaluable

## Biological Hypothesis

Competing biological explanation.

Question answered:

Which biological process best explains the evidence pattern?

Produces: Recommendation

Examples:
- Genuine tandem duplication
- Assembly artefact
- Partial assembly
- Chimeric contig

## Recommendation

Final action proposed by SegPick.

Examples:
- Select candidate
- Reject candidate
- Manual review
- Additional evidence required

---

# Knowledge Model

Measurements + Observation Rules = Observations

Observations + Interpretation Definitions = Interpretive Findings

Interpretive Findings + Evidence Pattern Definitions = Evidence Patterns

Evidence Patterns + Hypothesis Definitions = Biological Hypotheses

Biological Hypotheses + Recommendation Policy = Recommendation

Definitions are reusable knowledge.

Evaluations are candidate-specific reasoning.

---

# Reasoning Graph

The graph records scientifically meaningful reasoning objects only.

It is not an execution graph.

Relationships are represented exclusively by typed edges.

---

# Incomplete Reasoning

Incomplete reasoning is a valid scientific outcome.

Reasoning may terminate at Observation, Interpretive Finding, or Evidence Pattern when higher-level conclusions are not justified.

---

# Graph Pruning

Retain:
- Biological Hypotheses
- Evidence Patterns
- Interpretive Findings
- Scientifically meaningful Observations
- Supporting Measurements

Prune:
- Isolated measurement-only connected components

---

# Architectural View

Knowledge Base

- Observation Rules
- Interpretation Definitions
- Evidence Pattern Definitions
- Hypothesis Definitions
- Recommendation Policy

Reasoning pipeline

Measurement
→ Observation
→ Interpretive Finding
→ Evidence Pattern
→ Biological Hypothesis
→ Recommendation

The vertical axis represents candidate-specific reasoning.

The horizontal axis represents reusable biological knowledge.

Future extensions should add knowledge rather than change the reasoning architecture whenever possible.
