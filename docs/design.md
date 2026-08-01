# SegPick: Design Principles and System Architecture

**An explainable framework for evidence-based viral genome assembly curation**

> Living design document. This document describes the architectural philosophy
> of SegPick rather than its implementation details.

---

# Abstract

Genome assembly curation is traditionally a manual process in which multiple
sources of evidence—including sequence similarity, coding potential, read
support, structural consistency, and biological plausibility—are considered
simultaneously. Existing assembly evaluation tools typically reduce this
evidence to one or more numerical scores, leaving the reasoning process
implicit and often difficult to interpret.

SegPick adopts a different philosophy. Instead of attempting to replace expert
judgement with a single ranking metric, it models the reasoning process itself.
Independent evidence sources are first transformed into objective
**observations**. Observations are then combined into biological **findings**,
which in turn support explicit, rule-based **hypotheses**. Recommendations are
derived from these hypotheses while preserving complete traceability to the
underlying evidence.

By exposing rather than hiding the decision-making process, SegPick is intended
to function as a transparent computer-assisted biological curator rather than
an opaque scoring system.

---

# 1. Introduction

Segmented viral genomes frequently produce multiple competing contigs,
fragmented coding sequences and alternative assembly paths. Selecting the most
biologically plausible representation therefore requires integration of diverse
evidence rather than optimisation of a single metric.

Experienced curators naturally ask questions such as:

- Is the predicted protein complete?
- Is the coding sequence supported by sequencing reads?
- Does the candidate agree with related proteins?
- Are there indications of assembly interruption?
- Is the observed divergence biologically plausible?

SegPick formalises this reasoning process while deliberately keeping every
interpretation transparent.

---

# 2. Design Objectives

## 2.1 Explainability

Every recommendation should be explainable from observable evidence.

## 2.2 Modularity

Evidence channels should remain independent so new analyses can be added
without redesigning existing ones.

## 2.3 Conservatism

SegPick assists expert judgement rather than replacing it. Conflicting evidence
should lead to explicit manual review rather than overconfident automation.

## 2.4 Extensibility

Biological knowledge evolves. Interpretation should therefore be expressed as
rules rather than embedded procedural logic.

## 2.5 Reproducibility

Every analysis records software version, configuration, rule set and
provenance so results can be reproduced.

---

# 3. Separation of Measurement and Interpretation

A fundamental design principle is the separation between measurement and
biological interpretation.

```text
Raw evidence
      │
      ▼
Observations
      │
      ▼
Findings
      │
      ▼
Hypotheses
      │
      ▼
Recommendations
```

Each layer increases biological abstraction while preserving complete
traceability to the preceding layer.

---

# 4. Observations

Observations are objective statements derived directly from data. They contain
no biological interpretation.

Examples include:

- Complete open reading frame
- Internal stop codon
- Sustained coverage drop
- Protein alignment discontinuity
- High protein identity
- Expected segment length

Observations should remain valid regardless of the downstream interpretation.

---

# 5. Findings

Findings combine one or more observations into biologically meaningful
descriptions.

Examples include:

- Complete protein recovered
- Well-supported protein match
- Possible split assembly

Findings are descriptive interpretations, not recommendations.

---

# 6. Hypotheses

Hypotheses represent biological explanations inferred from findings.

SegPick generates hypotheses using explicit rules describing:

- Required evidence
- Supporting evidence
- Conflicting evidence

Each hypothesis records:

- originating rule
- supporting findings
- conflicting findings
- confidence
- rule source

Every hypothesis is therefore reproducible and explainable.

---

# 7. The Reasoning Engine

The reasoning engine is the conceptual core of SegPick.

Unlike conventional scoring systems, SegPick separates evidence acquisition from
knowledge application.

Evidence-producing analyses never decide biological meaning. They produce
observations only.

Independent rule sets then transform observations into findings and findings
into hypotheses.

This separation provides several advantages:

- biological knowledge evolves independently of analytical code;
- users can inspect every inference;
- laboratories can extend the knowledge base without modifying Python code;
- recommendations remain traceable to objective evidence.

Rule evaluation follows three simple concepts:

## Required conditions

Every required condition must be satisfied before a rule may generate a
hypothesis.

## Supporting conditions

Supporting conditions increase confidence but are not essential.

## Conflicting conditions

Conflicting evidence decreases confidence or suppresses an interpretation when
appropriate.

The rule engine therefore answers two separate questions:

1. *Should this biological interpretation exist?*
2. *How strongly is it supported?*

Rather than embedding expert judgement inside procedural code, SegPick stores
biological knowledge in an explicit, inspectable rule base. This makes the
reasoning process transparent, reproducible and extensible.

---

# Future sections

- Evidence Model
- Dashboard Philosophy
- Rule Explorer
- Analysis Manifest and Provenance
- Extensibility
- Future Directions
- Glossary
- References

