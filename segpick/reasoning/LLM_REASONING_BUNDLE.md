# LLM Reasoning Bundle

The LLM reasoning bundle is a deterministic, self-describing export of a candidate-specific SegPick reasoning graph.

The graph remains authoritative. LLM output is advisory and must be labelled speculative unless a human converts it into reviewed SegPick knowledge.

## Direction

Edges use hypothesis-first explanatory direction. For example, `A supported_by B` means that conclusion A is supported by evidence B.

## Uncertainty

Missing evidence is not contradictory evidence. An absent observation must not be interpreted as a negative observation.

## Recommended task

Ask the model to summarize graph-supported conclusions, identify unresolved evidence gaps, and propose alternative hypotheses while citing node IDs. Require output conforming to `llm_output.schema.json`.
