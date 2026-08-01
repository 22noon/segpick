# SegPick: Design Principles and System Architecture

**An explainable framework for evidence-based viral genome assembly
curation**

> Living design document describing the architectural philosophy of
> SegPick.

------------------------------------------------------------------------

# Abstract

Genome assembly curation is traditionally a manual process in which
multiple sources of evidence---including sequence similarity, coding
potential, read support, structural consistency, and biological
plausibility---are considered simultaneously. Existing assembly
evaluation tools typically reduce this evidence to one or more numerical
scores, leaving the reasoning process implicit and difficult to
interpret.

SegPick adopts a different philosophy. Instead of replacing expert
judgement with a single ranking metric, it models the reasoning process
itself. Independent evidence sources are transformed into
**observations**, observations are integrated into biological
**findings**, findings support explicit rule-based **hypotheses**, and
recommendations are derived while preserving complete traceability to
the underlying evidence.

By exposing rather than hiding the decision-making process, SegPick
functions as a transparent computer-assisted biological curator rather
than an opaque scoring system.

------------------------------------------------------------------------

# 1. Introduction

Segmented viral genomes frequently produce multiple competing contigs,
fragmented coding sequences and alternative assembly paths. Selecting
the most biologically plausible representation therefore requires
integration of diverse evidence rather than optimisation of a single
metric.

Experienced curators naturally ask questions such as:

-   Is the predicted protein complete?
-   Is the coding sequence supported by sequencing reads?
-   Does the candidate agree with related proteins?
-   Are there indications of assembly interruption?
-   Is the observed divergence biologically plausible?

SegPick formalises this reasoning process while deliberately keeping
every interpretation transparent.

------------------------------------------------------------------------

# 2. Design Objectives

## 2.1 Explainability

Every recommendation should be explainable from observable evidence.

## 2.2 Modularity

Evidence channels remain independent so new analyses can be added
without redesigning existing ones.

## 2.3 Conservatism

SegPick assists expert judgement rather than replacing it. Conflicting
evidence should lead to explicit manual review rather than overconfident
automation.

## 2.4 Extensibility

Biological knowledge evolves. Interpretation is therefore expressed as
explicit rules rather than embedded procedural logic.

## 2.5 Reproducibility

Every analysis records software version, configuration, rule set and
provenance so results can be reproduced.

------------------------------------------------------------------------

# 3. Separation of Measurement and Interpretation

A fundamental design principle is the separation between measurement and
biological interpretation.

``` text
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

------------------------------------------------------------------------

# 4. Observations

Observations are objective statements derived directly from data. They
contain no biological interpretation.

Examples include:

-   Complete open reading frame
-   Internal stop codon
-   Sustained coverage drop
-   Protein alignment discontinuity
-   High protein identity
-   Expected segment length

Observations remain valid regardless of downstream interpretation.

------------------------------------------------------------------------

# 5. Findings

Findings combine one or more observations into biologically meaningful
descriptions.

Examples include:

-   Complete protein recovered
-   Well-supported protein match
-   Possible split assembly

Findings are descriptive interpretations, not recommendations.

------------------------------------------------------------------------

# 6. Hypotheses

Hypotheses represent biological explanations inferred from findings.

SegPick generates hypotheses using explicit rules describing:

-   Required evidence
-   Supporting evidence
-   Conflicting evidence

Each hypothesis records its originating rule, supporting findings,
conflicting findings, confidence and rule source.

------------------------------------------------------------------------

# 7. The Reasoning Engine

The reasoning engine is the conceptual core of SegPick.

Evidence-producing analyses never decide biological meaning. They
produce observations only. Independent rule sets transform observations
into findings and findings into hypotheses.

This separation means:

-   biological knowledge evolves independently of analytical code;
-   users can inspect every inference;
-   laboratories can extend the knowledge base without modifying Python
    code;
-   recommendations remain traceable to objective evidence.

Rules distinguish:

## Required conditions

All required conditions must be satisfied.

## Supporting conditions

Supporting conditions strengthen confidence.

## Conflicting conditions

Conflicting evidence weakens or suppresses an interpretation.

The engine therefore answers two questions:

1.  Should this interpretation exist?
2.  How strongly is it supported?

------------------------------------------------------------------------

# 8. Why SegPick Is Not a Scoring System

Many assembly evaluation tools combine diverse evidence into a single
numerical score. While convenient, such scores obscure biological
reasoning by collapsing fundamentally different evidence types into one
value.

SegPick instead seeks first to explain the evidence. Ranking becomes a
consequence of biological reasoning rather than the primary objective.

Independent evidence channels remain interpretable, biological knowledge
is represented explicitly through rules, uncertainty is preserved
through manual-review recommendations, and every conclusion is traceable
to the original observations.

Consequently, SegPick should be viewed as an evidence-driven reasoning
framework rather than a scoring algorithm.

------------------------------------------------------------------------

# 9. Information Flow

``` text
Sequencing data
        │
        ▼
Analytical procedures
        │
        ▼
Measurements
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
        │
        ▼
Interactive interpretation
```

Information flows only in one direction. Higher-level interpretations
never modify lower-level evidence.

------------------------------------------------------------------------

# 10. Separation of Knowledge from Analysis

Analytical modules are deliberately knowledge-free. Coverage analysis
does not know what a split assembly is, and protein alignment does not
know what constitutes a complete segment. They report observations only.

All biological expertise resides in the rule base, allowing analytical
methods and biological knowledge to evolve independently.

------------------------------------------------------------------------

# 11. The Rule-Based Knowledge System

SegPick separates an analysis engine from a knowledge base. Analytical
procedures measure evidence; rules interpret evidence.

This allows laboratories to customise interpretation without modifying
the analytical components and treats biological expertise as data rather
than code.

> **Design rationale:** Biological knowledge changes faster than
> analytical methods. Explicit rules therefore improve transparency,
> extensibility and maintainability.

------------------------------------------------------------------------

# 12. Explainability and Traceability

Every recommendation can be traced through the complete reasoning chain:

``` text
Recommendation
      │
      ▼
Hypothesis
      │
      ▼
Finding
      │
      ▼
Observation
      │
      ▼
Original analytical evidence
```

The Rule Explorer embodies this philosophy by exposing both triggered
and non-triggered rules together with the evidence that supported or
prevented each interpretation.

> **Design rationale:** Explainability enables scientific discussion,
> not merely user confidence.

------------------------------------------------------------------------

# 13. Human-Centred Decision Support

SegPick is designed as a decision-support system rather than an
automated decision-making system.

Many biological datasets are genuinely ambiguous. SegPick therefore
preserves uncertainty through confidence estimates, supporting
hypotheses and explicit manual-review recommendations.

The dashboard is an interactive reasoning interface rather than simply a
report generator.

> **Design rationale:** Scientific software should augment expertise
> rather than obscure it.

------------------------------------------------------------------------

# Future Chapters

-   Evidence Model
-   Dashboard Philosophy
-   Analysis Manifest and Provenance
-   Design Decisions Rejected
-   Design Evolution
-   Extensibility
-   Future Directions
-   Glossary
-   References
