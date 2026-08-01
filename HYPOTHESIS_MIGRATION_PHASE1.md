# Hypothesis migration phase 1

This milestone begins migrating existing structural reasoning into the V3 reasoning graph without changing candidate ranking or recommendation logic.

## Declarative competing hypotheses

The built-in YAML knowledge base now includes:

- Reference-supported candidate architecture
- Possible repeated-sequence architecture
- Possible repeat-associated assembly artefact

The two repeated-mapping hypotheses intentionally share the same initiating observation. Read, cross-evidence, structural, and plugin observations then strengthen or challenge each explanation independently.

## Hypothesis state

Each emitted hypothesis now has a conservative evidence state:

- `provisional`: requirements matched, but no additional support or conflict matched
- `supported`: at least one supporting condition matched and no conflict matched
- `challenged`: conflict matched without additional support
- `contested`: both supporting and conflicting evidence matched

State is descriptive only. It does not alter scoring, ranking, or recommendation behaviour.

## Plugin propagation

Plugin observations can appear in `supports` or `conflicts` conditions by using their namespaced source, for example `plugin:junction_support`. When matched, they are retained in the hypothesis trace and V3 provenance graph.
