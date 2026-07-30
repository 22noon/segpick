# SegPick Evidence Interpretation Guide

**Version:** 1.0 (Draft)

**Applies to:** SegPick 1.x

---

# 1. Introduction

## Purpose

SegPick is an evidence-based curation framework for segmented viral genome assemblies.

Rather than relying on a single metric or ranking algorithm, SegPick evaluates multiple independent sources of biological evidence and combines them into an explainable recommendation. The objective is not simply to identify the highest-scoring contig, but to provide a transparent justification for every recommendation and to highlight situations where manual inspection is advisable.

Throughout the software, every recommendation is accompanied by the observations and biological interpretations that contributed to the final decision. Users are therefore able to inspect both the evidence supporting a recommendation and any evidence that argues against it.

SegPick is intended to assist biological curation rather than replace it.

---

# 2. Philosophy

## Multiple independent evidence sources

Genome assemblies can appear convincing when evaluated using a single metric while still containing structural errors.

For example,

- a contig may align well to a reference sequence but contain a truncated coding sequence,
- a complete ORF may be present despite poor read support,
- read coverage may strongly support a contig whose translated protein disagrees with the expected gene.

No individual measurement is sufficient to establish assembly correctness.

Instead, SegPick evaluates several independent evidence channels, including:

- protein similarity
- translated protein agreement (DIAMOND/BLASTX)
- ORF structure
- read support
- structural containment
- sequence identity
- fragmentation
- protein structural consistency

Agreement between independent evidence channels provides stronger support than any individual measurement alone.

---

## Observation, interpretation and recommendation

SegPick deliberately separates three different concepts.

### Observation

Observations are direct measurements made from the data.

Examples include

- protein identity = 99.2%
- complete ORF identified
- read depth = 385×
- one internal deletion of three amino acids

Observations are objective measurements and involve no biological interpretation.

---

### Interpretation

Interpretations describe what an observation may mean biologically.

For example,

Observation

    Complete ORF recovered.

Interpretation

    The expected coding sequence appears to be present.

Similarly,

Observation

    Multiple small internal indels.

Interpretation

    Pattern consistent with a possible frameshift or local assembly error.

Interpretations represent plausible biological explanations rather than definitive diagnoses.

---

### Recommendation

Recommendations combine multiple independent interpretations.

For example,

- protein evidence supports Candidate A,
- read support supports Candidate A,
- ORF structure supports Candidate A,
- BLASTX agreement supports Candidate A,
- no competing structural evidence is detected.

SegPick therefore recommends Candidate A.

Recommendations always include an explanation describing both the supporting evidence and any conflicting evidence.

---

# 3. Conservative interpretation

SegPick deliberately adopts conservative terminology.

For example, the software reports

    Possible frameshift pattern

rather than

    Frameshift detected.

Similarly,

    C-terminal truncation

does not imply that the truncation resulted from an assembly error.

Possible explanations include

- incomplete assembly,
- premature stop codon,
- sequencing artefacts,
- genuine biological variation.

Where multiple explanations remain plausible, SegPick reports the observed pattern while leaving biological interpretation to the user.

---

# 4. Explainable recommendations

Every recommendation produced by SegPick should answer four questions.

1. Why was this candidate selected?

2. What evidence supports the recommendation?

3. What evidence argues against the recommendation?

4. Should the assembly be manually reviewed?

The remainder of this guide describes how each evidence channel contributes to these questions and how the resulting biological interpretations are generated.

# 6. Protein Evidence

## Overview

Protein evidence evaluates whether a predicted coding sequence is consistent with the expected viral protein.

Unlike nucleotide alignments, protein alignments are less sensitive to synonymous nucleotide substitutions and therefore provide a more biologically meaningful assessment of coding sequence integrity.

SegPick compares the translated protein from the selected ORF against the protein sequence identified by the highest-scoring DIAMOND alignment (or an equivalent reference protein when DIAMOND information is unavailable).

Protein evidence contributes to both structural validation and the overall recommendation.

---

# Protein observations

SegPick measures several independent characteristics of the protein alignment.

## Protein identity

Protein identity measures the proportion of aligned amino acids that are identical.

High identity generally indicates that the predicted ORF encodes the expected viral protein.

Identity alone, however, does not guarantee that the protein is structurally complete.

---

## Protein coverage

Coverage describes how much of the expected reference protein is represented by the predicted ORF.

For example,

Reference

```
██████████████████████████████
```

Candidate

```
█████████████████████████████
```

indicates nearly complete recovery.

Conversely,

```
██████████████
```

suggests that only part of the expected protein has been recovered.

Coverage therefore complements identity by assessing completeness rather than sequence similarity.

---

## Gap residues

Gap residues represent amino acids inserted into or deleted from the alignment.

For example,

Reference

```
ABCDEFGHIJKLMN
```

Candidate

```
ABCDE---JKLMN
```

contains three deleted residues.

Gap residues quantify the total amount of inserted or deleted sequence but do not describe how those differences are distributed.

---

## Gap events

Gap events count the number of separate insertions or deletions.

For example,

One deletion

```
ABCDEFGHIJKLMN

ABCDE---JKLMN
```

contains

- Gap residues = 3
- Gap events = 1

whereas

```
AB-DEFG-IJKLM-
```

contains

- Gap residues = 3
- Gap events = 3

Although the total number of gap residues is identical, the biological interpretation is different.

Several small gap events are generally more suspicious than a single larger deletion because they may indicate local assembly errors or frameshifts.

---

## Largest internal indel

SegPick records the size of the largest insertion or deletion occurring within the alignment.

A single large indel may represent a genuine biological insertion or deletion.

Numerous small indels are more suggestive of sequencing or assembly artefacts.

---

# Protein interpretation

The observations above are combined into a structured biological interpretation.

Importantly, SegPick reports observations conservatively and avoids making unsupported biological claims.

---

## Complete protein

Observed pattern

- Complete N terminus
- Complete C terminus
- No internal indels

SegPick interpretation

```
Complete protein recovered.
```

Possible biological explanation

The expected coding sequence appears to have been assembled successfully.

---

## N-terminal truncation

Observed pattern

```
Reference

██████████████████████████████

Candidate

     █████████████████████████
```

SegPick interpretation

```
N-terminal truncation.
```

Possible explanations include

- incomplete assembly,
- incorrect ORF start,
- sequencing error,
- biological variation.

SegPick does not attempt to distinguish between these possibilities.

---

## C-terminal truncation

Observed pattern

```
Reference

██████████████████████████████

Candidate

██████████████████████
```

SegPick interpretation

```
C-terminal truncation.
```

Possible explanations include

- incomplete assembly,
- premature stop codon,
- sequencing artefacts,
- genuine biological shortening.

---

## Internal deletion

Observed pattern

```
██████████████████████

██████----████████████
```

SegPick interpretation

```
Internal deletion.
```

A single internal deletion does not necessarily indicate an assembly error.

The difference may represent either genuine biological variation or an assembly artefact.

---

## Internal insertion

Observed pattern

```
Reference

██████████████████████

Candidate

██████++++████████████
```

SegPick interpretation

```
Internal insertion.
```

As with deletions, SegPick reports the observation but does not infer the biological cause.

---

## Multiple scattered indels

Observed pattern

```
███-████-██-████-██
```

SegPick interpretation

```
Possible frameshift pattern.
```

SegPick deliberately uses the phrase *possible frameshift pattern*.

This wording reflects the fact that multiple scattered indels are consistent with a frameshift but do not prove that one has occurred.

Possible explanations include

- sequencing errors,
- local assembly artefacts,
- incorrect ORF prediction,
- genuine biological differences.

---

# Protein structural summary

The individual observations are combined into a structured
ProteinInterpretation object.

Typical structural summaries include

```
Complete protein recovered.
```

```
Protein contains terminal truncation.
```

```
Protein contains internal indel differences.
```

```
Protein contains terminal truncation and internal indels.
```

```
Possible frameshift pattern detected.
```

These summaries are intended to provide an overview of the observed structural characteristics rather than a definitive biological diagnosis.

---

# Contribution to recommendations

Protein evidence contributes to the recommendation in two ways.

First, it provides quantitative measurements including

- protein identity,
- protein coverage,
- structural consistency.

Second, it contributes qualitative biological interpretations that become part of the explanation shown in the dashboard.

When protein evidence conflicts with other evidence channels, SegPick records the disagreement explicitly rather than attempting to hide it inside a single numerical score.

---

# Inspecting protein evidence

The dashboard provides several tools for investigating protein evidence.

These include

- protein alignment viewer,
- predicted protein export,
- reference protein export,
- combined FASTA export,
- protein structural interpretation.

Users are encouraged to inspect the alignment directly whenever SegPick reports

- terminal truncation,
- multiple scattered indels,
- low protein coverage,
- or possible frameshift patterns.

Direct inspection of the alignment often provides additional biological insight beyond the summary classifications.

# 7. ORF Evidence

## Overview

Protein-coding genes are expected to contain an intact open reading frame (ORF). Consequently, the structure of the predicted ORF provides important evidence regarding the biological plausibility of an assembled contig.

Historically, many genome assembly pipelines selected the longest predicted ORF as the most likely coding sequence. While this approach is often effective, it can fail when assemblies contain sequencing errors, frameshifts, or multiple competing ORFs.

SegPick therefore uses protein evidence to guide ORF selection before evaluating ORF structure.

---

# ORF selection

## Protein-guided ORF selection

SegPick first predicts all plausible ORFs within a candidate contig.

When DIAMOND protein evidence is available, each predicted ORF is compared with the expected reference protein.

The ORF showing the strongest agreement with the expected protein is selected for subsequent analysis.

Selection considers several independent characteristics including

- protein identity,
- reference coverage,
- coordinate agreement,
- frame agreement,
- strand agreement,
- ORF completeness.

This strategy allows SegPick to select the biologically most plausible ORF rather than simply the longest ORF.

---

## Longest ORF

The longest ORF is still recorded for reference.

However, SegPick distinguishes between

- the longest ORF, and
- the biologically selected ORF.

When these differ, the dashboard reports both values.

This distinction helps identify situations where the longest ORF is unlikely to represent the expected viral gene.

---

# ORF observations

SegPick records several structural characteristics of the selected ORF.

These observations are reported independently before any biological interpretation is applied.

---

## Complete ORF

A complete ORF contains

- an appropriate initiation codon,
- a continuous coding sequence,
- and a termination codon.

A complete ORF generally provides stronger evidence for a biologically plausible coding sequence than a partial ORF.

---

## Partial ORF

Partial ORFs may arise when

- the contig is incomplete,
- the coding sequence extends beyond the assembled region,
- sequencing errors interrupt translation,
- or the predicted ORF is incorrect.

SegPick reports partial ORFs without attempting to determine the underlying cause.

---

## Complete ORF count

SegPick records the total number of complete ORFs identified within the candidate sequence.

The raw count is reported because it provides useful context but is not interpreted in isolation.

---

## Major competing ORFs

Small secondary ORFs occur frequently by chance and are common in viral genomes.

SegPick therefore distinguishes between

- incidental complete ORFs, and
- major competing ORFs.

A competing ORF is considered *major* when its translated protein length is at least 70% of the length of the selected ORF.

This threshold is intended to identify biologically plausible alternative coding sequences while ignoring small incidental ORFs.

---

## Largest competing ORF

SegPick records the length of the largest competing ORF.

This allows users to distinguish

```
Selected ORF

████████████████████████████

Competing ORF

███
```

from

```
Selected ORF

████████████████████████████

Competing ORF

█████████████████████████
```

Although both examples contain two complete ORFs, their biological interpretations are quite different.

---

# ORF interpretation

SegPick combines the structural observations into a biological interpretation.

---

## Complete coding sequence

Observed pattern

- complete ORF
- no major competing ORFs

SegPick reports

```
Complete coding sequence recovered.
```

Possible biological interpretation

The expected coding sequence appears structurally intact.

---

## Major competing ORF

Observed pattern

One or more competing ORFs satisfy the major ORF threshold.

SegPick reports

```
Major competing ORFs detected.
```

Possible explanations include

- overlapping genes,
- duplicated coding regions,
- chimeric assemblies,
- unexpected genome organisation.

SegPick does not attempt to distinguish between these possibilities.

Instead, the observation contributes to the structural evidence and may increase the likelihood that manual review is recommended.

---

## Selected ORF differs from longest ORF

Observed pattern

The selected ORF is not the longest predicted ORF.

SegPick reports both ORFs separately.

Possible explanations include

- the longest ORF is unrelated to the expected viral protein,
- the selected ORF provides much stronger protein agreement,
- sequencing or assembly errors have altered ORF lengths.

The biologically selected ORF is always used for downstream protein analysis.

---

# Contribution to recommendations

ORF evidence contributes to several aspects of the recommendation process.

These include

- ORF completeness,
- presence of competing ORFs,
- agreement with protein evidence,
- structural plausibility.

Importantly, ORF evidence is evaluated alongside independent evidence channels rather than in isolation.

---

# Inspecting ORF evidence

The dashboard displays

- the selected ORF,
- strand,
- reading frame,
- nucleotide coordinates,
- competing ORFs,
- ORF structural interpretation.

Users should inspect ORF evidence carefully whenever SegPick reports

- partial ORFs,
- major competing ORFs,
- disagreement between the selected and longest ORF,
- or conflicts with BLASTX evidence.

The ORF diagram, protein alignment and read-coverage plot together provide complementary views of coding sequence integrity.

# 8. Protein Homology Evidence (DIAMOND / BLASTX)

## Overview

Protein homology provides one of the strongest independent sources of evidence for evaluating a candidate assembly.

SegPick compares translated coding sequences against a curated protein reference database using DIAMOND BLASTX (or an equivalent translated protein search).

Unlike nucleotide alignments, translated alignments are comparatively insensitive to synonymous nucleotide substitutions and therefore provide a robust assessment of whether a candidate encodes the expected viral protein.

Protein homology evidence serves two distinct purposes within SegPick.

First, it guides selection of the biologically most plausible ORF.

Second, it contributes independent evidence to the recommendation process.

These two roles should be considered separately.

---

# Protein homology observations

SegPick records several characteristics of the highest-scoring translated alignment.

These measurements are reported directly without biological interpretation.

---

## Best matching protein

The highest-scoring protein identified by DIAMOND is retained as the expected protein for downstream comparison.

The corresponding protein sequence is used for

- ORF selection,
- protein alignment,
- structural interpretation,
- dashboard visualisation.

---

## Protein identity

Protein identity measures the proportion of identical amino acids within the translated alignment.

Higher identity generally indicates greater similarity to the expected viral protein.

Identity alone, however, does not establish that the predicted coding sequence is structurally correct.

---

## Subject coverage

Subject coverage measures how much of the reference protein is represented by the translated alignment.

High subject coverage suggests that the predicted ORF spans most of the expected protein.

Low coverage may indicate

- partial assemblies,
- truncated ORFs,
- fragmented coding sequences.

---

## Query coverage

Query coverage measures how much of the predicted protein contributes to the translated alignment.

This complements subject coverage by identifying situations in which substantial portions of the predicted ORF fail to align to the expected protein.

---

## Reading frame

DIAMOND identifies the translated reading frame used by the alignment.

SegPick compares this frame with the frame of the selected ORF.

Agreement between the two provides strong evidence that the selected ORF represents the expected coding sequence.

---

## Strand

SegPick also compares strand orientation.

Agreement between the translated alignment and the selected ORF increases confidence that the correct coding sequence has been identified.

---

## Alignment coordinates

The translated alignment provides approximate coordinates for the coding region.

These coordinates are compared with the selected ORF.

Agreement between the two supports the biological plausibility of the ORF prediction.

---

# Protein homology interpretation

The observations above are interpreted conservatively.

---

## Excellent agreement

Observed pattern

- same strand
- same reading frame
- excellent coordinate agreement
- high protein identity
- high subject coverage

SegPick reports

```
Excellent protein homology agreement.
```

Possible interpretation

The selected ORF is highly consistent with the expected viral protein.

---

## Frame disagreement

Observed pattern

Selected ORF and translated alignment use different reading frames.

SegPick reports

```
Frame disagreement.
```

Possible explanations include

- incorrect ORF prediction,
- sequencing errors,
- local assembly artefacts,
- genuine biological differences.

Frame disagreement does not automatically indicate an assembly error but is considered an important source of conflicting evidence.

---

## Strand disagreement

Observed pattern

Selected ORF and translated alignment occur on opposite strands.

SegPick reports

```
Strand disagreement.
```

Possible explanations include

- incorrect ORF selection,
- assembly artefacts,
- unusual genome organisation.

Such cases generally warrant manual inspection.

---

## Coordinate disagreement

Observed pattern

The translated alignment and selected ORF occupy substantially different regions of the contig.

SegPick reports

```
Coordinate disagreement.
```

This pattern suggests that the selected ORF may not correspond to the translated protein identified by DIAMOND.

---

## Low protein coverage

Observed pattern

Only a small fraction of the expected protein is recovered.

SegPick reports

```
Incomplete protein recovery.
```

Possible explanations include

- truncated assemblies,
- fragmented ORFs,
- sequencing artefacts,
- incorrect candidate selection.

---

# Protein-guided ORF selection

One of the defining features of SegPick is that protein homology evidence contributes directly to ORF selection.

Rather than selecting the longest predicted ORF, SegPick evaluates each candidate ORF against the expected protein identified by DIAMOND.

The ORF demonstrating the strongest overall agreement is selected for downstream analysis.

Protein homology therefore influences ORF selection before any recommendation is generated.

---

# Contribution to recommendations

Protein homology contributes independently to the recommendation engine.

It evaluates whether the predicted coding sequence agrees with an external biological expectation.

Agreement between protein homology and other evidence channels increases confidence in the recommendation.

Disagreement does not automatically invalidate a candidate, but it is recorded explicitly and may contribute to a recommendation for manual review.

---

# Inspecting protein homology evidence

The dashboard provides several tools for investigating protein homology.

These include

- translated protein alignment,
- reference protein sequence,
- predicted protein sequence,
- downloadable FASTA files,
- protein structural interpretation.

Users should inspect the translated alignment whenever SegPick reports

- frame disagreement,
- strand disagreement,
- coordinate disagreement,
- incomplete protein recovery,
- or conflicts with ORF evidence.

Direct inspection often provides additional biological insight beyond the summary interpretation.

# 9. Read-support Evidence

## Overview

Read support provides direct experimental evidence for the assembled nucleotide sequence.

Unlike protein homology or ORF prediction, which infer biological plausibility, read support evaluates how well the sequencing data support the assembled contig itself.

SegPick therefore treats read support as an independent evidence channel.

Agreement between read support and structural evidence increases confidence in a recommendation.

Disagreement between these evidence sources may indicate regions that warrant closer inspection.

---

# Read-support observations

SegPick derives read-support evidence from read alignments generated against each candidate contig.

The following measurements are currently considered.

---

## Coverage depth

Coverage depth measures the number of sequencing reads aligned to each nucleotide position.

For example,

```
████████████████████████████
```

indicates relatively uniform support across the contig.

Coverage depth alone does not establish assembly correctness but provides useful context when interpreted alongside other evidence.

---

## Coverage completeness

Coverage completeness describes whether read support extends across the entire coding sequence.

For example,

```
████████████████████████████
```

suggests that the assembled region is consistently supported.

In contrast,

```
█████████████
```

may indicate that only part of the predicted coding region is well supported.

---

## Coverage uniformity

SegPick examines whether coverage varies substantially across the predicted coding sequence.

Uniform coverage generally provides stronger support than highly uneven coverage.

Large fluctuations may arise from

- amplification bias,
- sequencing bias,
- repetitive sequence,
- assembly artefacts,
- or genuine biological variation.

Coverage variation should therefore be interpreted cautiously.

---

## ORF annotation

Coverage plots display the location of the selected ORF directly beneath the coverage profile.

This allows users to determine whether regions of poor read support coincide with the predicted coding sequence.

For example,

```
Coverage

██████████████████████████

Selected ORF

▶────────────────────────▶
```

A reduction in coverage outside the coding sequence is often less concerning than a comparable reduction occurring within the ORF itself.

---

# Read-support interpretation

SegPick reports qualitative interpretations of the observed coverage patterns.

These interpretations are intended to guide manual inspection rather than diagnose assembly errors.

---

## Uniform read support

Observed pattern

- relatively even coverage
- complete support across the ORF

SegPick reports

```
Uniform read support across the coding sequence.
```

Possible interpretation

The sequencing reads consistently support the assembled coding region.

---

## Terminal coverage reduction

Observed pattern

Coverage decreases near one end of the predicted ORF.

Example

```
██████████████▇▅▂
```

Possible explanations include

- incomplete assembly,
- reduced sequencing coverage,
- terminal assembly uncertainty,
- library preparation bias.

SegPick reports the observed pattern without inferring a specific cause.

---

## Internal coverage reduction

Observed pattern

```
██████▂▂▂██████
```

Possible explanations include

- local assembly uncertainty,
- repetitive sequence,
- mapping ambiguity,
- sequencing artefacts.

When an internal coverage reduction coincides with protein differences or ORF abnormalities, users are encouraged to inspect the affected region more closely.

---

## Coverage disagreement

Read-support evidence may occasionally favour a different candidate from that selected by other evidence channels.

For example,

- Candidate A has the strongest protein evidence.
- Candidate B has consistently higher read support.

SegPick records this disagreement explicitly rather than allowing one evidence source to override the other automatically.

Such situations commonly result in a recommendation for manual review.

---

# Contribution to recommendations

Read support contributes independently to the recommendation process.

Its role is to evaluate whether the sequencing data support the proposed assembly.

Importantly, read support is considered alongside other evidence channels.

High read support does not compensate for severe structural inconsistencies, and excellent structural evidence does not automatically outweigh poor read support.

Instead, SegPick records both forms of evidence and explains any disagreements.

---

# Inspecting read-support evidence

The dashboard provides several tools for examining read support.

These include

- coverage plots,
- ORF annotations,
- candidate-specific coverage,
- combined read-support summaries.

Users should inspect read support whenever SegPick reports

- terminal coverage loss,
- internal coverage reductions,
- disagreement with protein evidence,
- disagreement with ORF evidence,
- or recommendations for manual review.

Particular attention should be paid to regions where multiple evidence channels indicate the same area of the assembly.

For example, a local reduction in read coverage that coincides with a protein insertion or deletion provides stronger evidence that the affected region merits further investigation than either observation alone.

# 10. Evidence Synthesis

## Overview

Each evidence channel evaluated by SegPick describes one aspect of assembly quality.

For example,

- protein homology evaluates similarity to the expected viral protein,
- ORF evidence evaluates coding sequence integrity,
- read support evaluates experimental support from the sequencing data,
- structural containment evaluates completeness relative to other candidate sequences.

Each channel provides useful information, but no single channel is sufficient to determine whether an assembly is biologically correct.

SegPick therefore combines multiple independent evidence channels into an overall recommendation.

The recommendation process is intended to be transparent and explainable.

Rather than relying on a single score, SegPick records

- supporting evidence,
- conflicting evidence,
- biological interpretations,
- recommendation confidence,
- manual-review suggestions.

---

# Independent evidence

The evidence channels are deliberately designed to be as independent as possible.

For example,

```
Protein evidence
```

asks

> Does this sequence encode the expected protein?

whereas

```
Read support
```

asks

> Do the sequencing reads support this nucleotide sequence?

Neither question answers the other.

Agreement between independent evidence channels therefore provides stronger support than repeated measurements of the same characteristic.

---

# Evidence convergence

One of the central concepts used throughout SegPick is **evidence convergence**.

Evidence convergence occurs when two or more independent evidence channels identify compatible observations affecting the same candidate or the same genomic region.

For example,

```
Protein alignment

↓

Internal deletion

-------------------------

Read support

↓

Coverage reduction

-------------------------

ORF evidence

↓

Partial coding sequence
```

Together these observations provide stronger evidence that the affected region merits investigation than any single observation considered in isolation.

Evidence convergence does **not** establish that an assembly error has occurred.

Instead, it increases confidence that the observed pattern is biologically meaningful and should be examined more closely.

---

# Evidence disagreement

Evidence channels do not always agree.

For example,

Protein evidence may strongly favour one candidate while read support favours another.

Similarly,

ORF structure may suggest a complete coding sequence while protein homology indicates poor agreement with the expected viral protein.

Rather than forcing these observations into a single numerical score, SegPick records the disagreement explicitly.

Evidence disagreement contributes to

- recommendation confidence,
- manual-review suggestions,
- candidate comparison,
- dashboard explanations.

---

# Weighted evidence

Each evidence channel contributes to the overall recommendation using configurable weights.

These weights reflect the relative contribution of each evidence source.

Weights are intended to represent biological importance rather than statistical confidence.

If one evidence channel is unavailable, its weight is redistributed across the remaining evidence channels.

This prevents candidates from being penalised simply because one source of evidence could not be evaluated.

---

# Supporting evidence

Supporting evidence consists of observations that favour the recommended candidate.

Examples include

- highest protein confidence,
- complete ORF,
- excellent protein agreement,
- strong read support,
- structurally complete sequence.

Supporting evidence is reported explicitly within the dashboard.

---

# Conflicting evidence

Conflicting evidence consists of observations that favour an alternative candidate or suggest that the recommendation should be interpreted cautiously.

Examples include

- stronger read support for another candidate,
- competing major ORFs,
- truncated coding sequence,
- frame disagreement,
- incomplete protein recovery.

Conflicting evidence is displayed separately from supporting evidence.

This allows users to distinguish between

```
Strong recommendation

with

minor caveats
```

and

```
Weak recommendation

with

major evidence conflicts.
```

---

# Recommendation confidence

Confidence describes the overall agreement between evidence channels.

Importantly,

confidence does **not** represent a statistical probability.

Instead, confidence reflects how consistently the available evidence supports the recommended candidate.

Typical interpretations are

High confidence

Most evidence channels independently support the same candidate.

Medium confidence

One or more important evidence channels disagree.

Low confidence

Several independent evidence channels provide conflicting conclusions.

---

# Manual review

Manual review is recommended whenever evidence disagreement exceeds predefined thresholds.

Examples include

- major competing ORFs,
- strong protein disagreement,
- conflicting read support,
- conflicting structural evidence.

The purpose of manual review is not to reject the recommendation but to encourage closer inspection of the affected candidate.

---

# Explainable recommendations

Every recommendation produced by SegPick is intended to answer four questions.

```
Why was this candidate selected?

↓

What evidence supports it?

↓

What evidence argues against it?

↓

Should the result be reviewed manually?
```

The dashboard, JSON reports and evidence summaries are all generated from the same underlying recommendation model.

Consequently, the explanation presented to the user remains consistent regardless of how the results are viewed.

---

# Future directions

The evidence synthesis framework has been designed to accommodate additional evidence channels.

Potential future extensions include

- conserved protein domains,
- long-read support,
- graph-based assembly evidence,
- transcript evidence,
- synteny,
- comparative genomics.

Because evidence, interpretation and recommendation are treated as separate stages, new evidence channels can be incorporated without redesigning the overall recommendation framework.

# 11. Conclusions

SegPick was designed around a simple principle:

Recommendations should be understandable.

Rather than hiding biological judgement inside a single numerical score,
SegPick exposes the observations, interpretations and evidence that
contribute to every recommendation.

Users are therefore able to

- inspect the supporting evidence,
- understand conflicting observations,
- review alternative candidates,
- and make informed biological decisions.

SegPick is intended to support biological curation rather than replace it.

Ultimately, the software provides an evidence-based framework for
understanding genome assemblies, while recognising that biological
interpretation remains the responsibility of the investigator.
