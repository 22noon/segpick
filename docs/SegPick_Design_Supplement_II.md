# SegPick Design Principles and System Architecture

## Supplement II: Scientific Philosophy and Knowledge Evolution

This supplement continues the architectural design document and focuses
on the scientific philosophy underlying SegPick.

------------------------------------------------------------------------

# 14. The Philosophy of Evidence

One of the central principles underlying SegPick is that evidence is not
synonymous with certainty.

Different analytical procedures measure different properties of an
assembly. Protein similarity, read coverage, coding potential,
structural continuity and reference agreement each describe distinct
aspects of the available data. No single measurement is sufficient to
establish biological correctness, nor does disagreement between evidence
sources necessarily imply that one of them is wrong.

SegPick therefore treats each evidence channel as an independent
observation of biological reality.

The objective is not to maximise agreement between evidence sources, but
rather to preserve their individuality so that concordance and
disagreement can both contribute meaningfully to biological
interpretation.

This philosophy has important consequences.

-   Evidence is accumulated rather than averaged.
-   Conflicting evidence is regarded as informative rather than
    problematic.
-   Uncertainty is preserved until explicitly resolved by biological
    rules.

### Design rationale

Evidence should remain independent for as long as possible. Information
discarded during early stages of analysis cannot be recovered later.

------------------------------------------------------------------------

# 15. Evidence Convergence

SegPick distinguishes between the existence of evidence and the
convergence of evidence.

Several independent observations supporting the same biological
interpretation provide stronger justification than repeated measurements
of a single analytical property.

For example, uninterrupted protein alignment, continuous read coverage
and an expected segment length represent three independent observations.
Together they provide substantially stronger support than any single
observation considered alone.

Evidence convergence therefore represents agreement between independent
analytical perspectives rather than accumulation of numerical scores.

### Design rationale

Independence of evidence is more valuable than quantity of evidence.

------------------------------------------------------------------------

# 16. Recommendations and Uncertainty

SegPick deliberately distinguishes between interpretation and decision.

A hypothesis represents a possible biological explanation.

A recommendation represents the current best course of action.

These concepts are related but not identical.

Several competing hypotheses may exist simultaneously while still
leading to a single recommendation that manual review is required.

SegPick therefore models uncertainty explicitly rather than attempting
to eliminate it.

### Design rationale

Biological ambiguity is often genuine. Representing uncertainty is
preferable to replacing it with unwarranted certainty.

------------------------------------------------------------------------

# 17. Conservatism by Design

Throughout its architecture, SegPick adopts a conservative approach to
inference.

Rules generate hypotheses only when supported by explicit evidence.
Recommendations favour manual review whenever competing explanations
remain plausible.

The aim is to minimise false confidence rather than maximise automated
decision-making.

### Design rationale

A transparent recommendation requiring expert review is preferable to an
opaque automated decision presented with unjustified certainty.

------------------------------------------------------------------------

# 18. Knowledge as a Community Resource

SegPick treats biological knowledge as a resource that evolves
independently of the software implementation.

Rules represent explicit biological expertise contributed by users,
laboratories and future collaborators.

As new viral lineages, assembly artefacts and biological phenomena are
encountered, corresponding interpretations can be incorporated into the
rule base without redesigning the analytical framework.

Software eventually becomes obsolete. Explicit biological knowledge can
continue to evolve and remain valuable across successive generations of
analytical methods.

### Design rationale

The enduring value of SegPick lies not only in its analytical algorithms
but also in the accumulated biological knowledge encoded within its rule
library.

------------------------------------------------------------------------

# 19. Scientific Reasoning as a Layered Process

Scientific interpretation rarely proceeds directly from observations to
conclusions. Instead, increasingly abstract conceptual layers are
constructed.

``` text
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
```

Each layer answers a distinct question:

-   Measurements: What was detected?
-   Observations: What objective facts can be stated?
-   Findings: What biological patterns are present?
-   Hypotheses: What biological explanations are plausible?
-   Recommendations: What action should the curator take?

### Design rationale

Different questions should be answered at different levels of
abstraction.

------------------------------------------------------------------------

# 20. The Role of the Human Curator

SegPick is intended to reduce repetitive analytical work while
preserving those aspects of genome interpretation requiring scientific
judgement.

The software performs objective computational tasks such as alignment,
ORF prediction, evidence extraction, rule evaluation and provenance
recording.

The curator evaluates unexpected observations, conflicting evidence and
novel biological phenomena.

Automation expands expert capability rather than replacing expertise.

### Design rationale

The purpose of automation is to organise evidence, not to substitute for
scientific reasoning.

------------------------------------------------------------------------

# 21. Learning from Exceptional Cases

SegPick is intentionally designed to learn from unusual datasets.

Novel viral lineages, unexpected protein structures and previously
unseen assembly artefacts are opportunities to extend the knowledge base
rather than failures of the system.

Exceptional cases become new regression datasets and potential additions
to the rule library.

### Design rationale

Exceptional cases often contribute more to scientific understanding than
routine analyses.

------------------------------------------------------------------------

# 22. Knowledge Evolution

SegPick assumes that biological knowledge will evolve indefinitely.

Rules are expected to be refined, expanded and occasionally retired as
understanding improves.

Because every analysis records provenance, historical results remain
reproducible while allowing future reinterpretation.

### Design rationale

Scientific software should evolve by accumulating knowledge rather than
repeatedly redesigning its analytical foundations.

------------------------------------------------------------------------

# 23. Towards a General Framework for Explainable Bioinformatics

Although developed for segmented viral genome assembly curation, the
underlying architectural principles are broadly applicable.

Potential future applications include:

-   microbial genome finishing
-   plasmid reconstruction
-   metagenomic bin validation
-   structural variant interpretation
-   comparative genome annotation
-   clinical variant interpretation

SegPick should therefore be viewed as the first implementation of a more
general framework for explainable biological reasoning.

### Design rationale

Architectural principles should outlive individual software
implementations.

------------------------------------------------------------------------

# 24. Concluding Perspective

SegPick originated as a practical tool for selecting among competing
viral assembly contigs.

During its development it evolved into an explicit framework for
representing biological reasoning.

Measurements became observations.

Observations became findings.

Findings generated hypotheses.

Hypotheses informed recommendations.

Every stage remained visible, inspectable and reproducible.

The long-term success of the project will depend not only upon
improvements in analytical algorithms but also upon the continued
refinement and sharing of the biological knowledge they help reveal.
