# SegPick scope

## Current scope

SegPick currently targets segmented viral genomes in which each segment is
evaluated using one primary gene or coding target.

For every gene/segment, SegPick:

- groups candidate contigs;
- associates reference sequences;
- evaluates structural alignment;
- normalises independent evidence channels;
- ranks candidates;
- produces an explainable recommendation.

Bluetongue virus is the initial supported use case.

## Deferred scope

Segments containing multiple genes, overlapping ORFs, alternative coding
strategies, or complex gene-order constraints are not yet modelled explicitly.

Supporting those genomes may require:

- a segment-level domain object;
- multiple gene or ORF annotations per candidate;
- per-gene completeness metrics;
- gene-order and orientation validation;
- combined gene-level and segment-level scoring.

These features should extend the current evidence architecture rather than
changing the meaning of existing evidence channels.
