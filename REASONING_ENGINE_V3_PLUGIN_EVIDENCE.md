# Reasoning Engine V3: plugin evidence foundation

This milestone adds an immutable reasoning graph alongside the existing SegPick reasoning objects. Existing dashboard behaviour, scoring, observations, findings, hypotheses, and recommendations remain unchanged.

## Graph layers

Each candidate can now expose:

- `MeasurementNode`
- `ObservationNode`
- `InterpretationNode`
- `HypothesisNode`
- `ReasoningGraph`

The graph validates globally unique node identifiers and all downward provenance references.

## Plugin evidence channels

A plugin evidence channel implements the `EvidenceChannel` protocol and returns an `EvidencePluginResult` containing:

- measurements
- observations

Plugin observation sources use the namespace `plugin:<channel_id>`. Declarative hypothesis rules can match these sources in exactly the same way as built-in evidence sources.

The path is:

`plugin measurement -> plugin observation -> interpretation/hypothesis`

Plugin measurements and graph output are included in candidate JSON reports under `reasoning_graph`.

## Compatibility

The V3 graph is constructed alongside the existing reasoning representation. No current inference rule or recommendation behaviour is replaced in this phase.

## Tests

The test suite verifies:

- plugin registration
- duplicate channel rejection
- plugin measurement creation
- plugin observation attachment
- plugin-triggered hypothesis evaluation
- measurement-to-observation provenance
- observation-to-hypothesis provenance
- graph validation
