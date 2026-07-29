# Reasoning Engine v2

SegPick cross-evidence reasoners can now express scientific evidence synthesis rather than binary rule firing.

## Structured output

A v2 finding records:

- weighted supporting contributions;
- contradictory contributions;
- evidence that was expected but unavailable;
- numeric and categorical confidence;
- evidence completeness;
- complete, partial, or contested match status;
- confidence method and version;
- complete rule and plug-in provenance.

## Backward compatibility

Existing plug-ins returning `CrossEvidenceFinding` continue to work. Legacy evidence references are automatically represented as unweighted structured contributions. New plug-ins may use `StructuredCrossEvidenceRule` and `ContributionSpec`.

## Confidence calculation

The built-in v2 reasoner calculates a weighted mean of the confidence of present supporting channels, scales it by evidence completeness, and subtracts weighted contradictory evidence. Missing evidence reduces completeness but is not treated as evidence against the interpretation.

This transparent calculation is intentionally conservative and versioned as `weighted_evidence_contributions` v2.0. It may be replaced by another reasoner-specific method while preserving the same output contract.

## Partial matching

Reasoners are strict by default. A plug-in must explicitly set `allow_partial=True` and define `minimum_required_fraction` before an incomplete pattern can generate a finding. Partial results are labelled clearly and cannot affect ranking by default.
