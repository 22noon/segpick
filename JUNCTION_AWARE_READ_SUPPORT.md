# Junction-aware read support

SegPick now separates two questions for candidate sequence absent from the
closest reference:

1. **Sequence authenticity** — is the reference-absent interval represented by
   regional read depth?
2. **Placement authenticity** — does read depth remain locally smooth across
   the left and right attachment points?

## Measurements

For each internal gap between reference-aligned candidate blocks, SegPick
records:

- regional median depth and zero-depth fraction;
- left and right outer-flank median depth;
- left and right inner-interval median depth;
- a balanced depth ratio for each junction;
- whether each junction is smooth at the configured threshold.

The default junction window is 10 nt and the default smoothness threshold is a
smaller/larger median-depth ratio of 0.5.

## Interpretations

- Regional support plus smooth depth at both junctions supports the assembled
  placement.
- Regional support plus a discontinuity at either junction suggests that the
  sequence may be genuine while its placement is uncertain.
- Weak regional support raises concern that the interval itself may be
  unsupported.

## Important limitation

These measurements use a samtools depth profile. Smooth depth does not prove
that individual reads or read pairs span a junction. Confirmation should use
read-level alignments, paired-end consistency, split-read evidence, long reads,
or assembly-graph inspection.

The junction evidence channel is explanatory and does not participate in
candidate ranking.
