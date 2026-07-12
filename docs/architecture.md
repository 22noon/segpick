# Architecture

The basic unit of analysis is the BTV gene/segment.

```text
Sample
  Gene
    CandidateContig
    ReferenceSequence
    Alignment
```

## v0.2 alignment logic

For each gene:

1. Candidate contigs and BLAST-selected references are written to `gene_fastas/<gene>.fa`.
2. The longest sequence among candidates and references is selected as the anchor.
3. The anchor is written to `anchors/<gene>.anchor.fa`.
4. `minimap2 -x asm5 -c anchor.fa gene.fa` is run.
5. PAF alignments are parsed into `Alignment` objects and attached to the `Gene`.
