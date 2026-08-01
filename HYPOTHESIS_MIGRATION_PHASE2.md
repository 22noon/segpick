# Hypothesis migration phase 2

This milestone preserves the full declarative identity and provenance of evaluated hypotheses inside the immutable V3 reasoning graph.

## Preserved hypothesis metadata

Each `HypothesisNode` now retains:

- category
- scope
- severity
- rule source
- rule description
- rule references

The earlier graph retained the hypothesis title, summary, confidence, evidence links, rule ID, and state, but discarded this additional rule metadata during conversion from `BiologicalHypothesis` to `HypothesisNode`.

## Behaviour

This is a behaviour-preserving migration. It does not alter:

- rule matching
- hypothesis confidence or state
- candidate scoring
- ranking
- recommendation logic

The additional fields are available in graph JSON and therefore in the Expert-tab graph inspector and downloaded reasoning graph. This makes each hypothesis traceable not only to evidence nodes but also to the declarative knowledge source that created it.
