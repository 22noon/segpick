# Structural Alignment Explorer — Phase 2

This milestone adds a candidate-centric architecture model derived from ordered MegaBLAST HSPs.

## Candidate architecture model

Each HSP is preserved as an independent block and ordered by candidate coordinates. The exported architecture records:

- candidate and reference intervals
- strand
- query gap preceding the block
- repeated-reference involvement
- nucleotide identity and bitscore

The architecture summary conservatively classifies directly observable patterns:

- single alignment block
- collinear architecture
- fragmented collinear architecture
- mixed-orientation architecture
- reordered reference progression
- repeated-reference architecture

These labels are structural observations, not automatic claims of biological chimerism.

## Visualization

The closest-reference figure now contains:

1. candidate-to-reference HSP dot plot
2. candidate architecture track ordered along the contig
3. individual HSP lanes when repeated-reference mappings are present

Forward blocks are blue, reverse-orientation blocks are purple, and repeated-reference blocks are orange dashed traces. Hover details connect each candidate block to its reference interval.

## Dashboard integration

The plot summary now reports the primary architecture classification and the number of substantial internal gaps. Architecture blocks and summaries are also available in the dashboard payload for later reasoning and interactive highlighting.

## Validation

`PYTHONPATH=. pytest -q`

Result: `207 passed`.
