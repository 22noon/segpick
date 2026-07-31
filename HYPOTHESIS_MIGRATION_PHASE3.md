# Hypothesis Migration Phase 3: Interpretive Findings

This increment introduces `InterpretiveFindingNode` as the canonical immutable graph class for the layer between observations and evidence synthesis.

The reasoning chain is now named conceptually as:

```text
Measurement
    -> Observation
    -> Interpretive Finding
    -> Scenario / future Evidence Synthesis
    -> Biological Hypothesis
```

## Compatibility

`InterpretationNode` remains available as a temporary alias of `InterpretiveFindingNode`. Existing code and external imports therefore continue to work while new code can adopt the clearer scientific terminology.

The `ReasoningGraph.interpretations` collection and the `interpretations` JSON key are intentionally retained in this increment. Renaming the container and serialized key will be handled separately so that downstream dashboard and API consumers can migrate deliberately.

## Behaviour

This is a terminology and type migration only. It does not change:

- evidence extraction;
- rule evaluation;
- scenario evaluation;
- hypothesis confidence or state;
- ranking; or
- recommendations.
