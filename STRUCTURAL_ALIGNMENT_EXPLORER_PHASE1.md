# Structural Alignment Explorer — Phase 1

This milestone makes repeated-reference mappings explicit in the closest-reference dot plot.

## Changes

- Preserves every MegaBLAST HSP as an independently inspectable trace.
- Detects pairs of non-overlapping candidate intervals that overlap on the reference.
- Draws diagnostic HSPs last as thicker orange dashed traces with endpoint markers.
- Shades each overlapping reference interval.
- Adds a separate candidate-coordinate HSP track so shorter blocks cannot be hidden by drawing order.
- Reports repeated-reference pair count and affected reference span in the plot summary.
- Links provenance to the highlighted structural-alignment view.
- Clarifies the observation label to refer to separate candidate regions.

The diagnostic pairing uses the same interval criterion as the reference-compatibility duplication assessment.
