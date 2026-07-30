# Cross-Evidence Rule Plug-ins

Cross-evidence rules consume stable `EvidenceAssessment` objects and emit `CrossEvidenceFinding` objects. They do not access channel-specific analysis implementations and are explanatory by default.

## Python contract

A rule exposes `rule_id`, `version`, `source_plugin`, `required_channels`, and `evaluate(context)`. Register built-in or local rules with `register_rule(rule)`.

External packages may publish rules through:

```toml
[project.entry-points."segpick.cross_evidence_rules"]
my_rules = "my_package.rules:rules"
```

The entry point may return one rule or a sequence of rules. Rules should use namespaced identifiers such as `my_lab:long_read_spanning_support`.

## Stable inputs

`CrossEvidenceContext` provides:

- all evidence assessments for one candidate;
- candidate and gene identifiers;
- lookup of assessments by channel ID;
- lookup of findings by channel ID and stable finding ID.

Rules must not depend on dashboard labels or private analysis attributes.

## Provenance and safety

Every result records rule ID and version, source plug-in, supporting and conflicting evidence, confidence, limitations, and ranking participation. Cross-evidence findings do not affect ranking unless a future explicit configuration grants that permission.
