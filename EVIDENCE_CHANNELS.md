# SegPick evidence-channel contract

Every evidence channel returns one `EvidenceAssessment`. The assessment separates:

- **score**: direction and strength of the biological evidence;
- **confidence**: reliability of that assessment;
- **key finding**: the highest-priority biological interpretation;
- **provenance**: confidence factors, measurements, limitations and method version.

Confidence must not be inferred solely from the channel score. Each channel documents a named, versioned confidence method and the factors used to calculate it.

## Built-in channel registration

Built-in channels use `@register_channel("channel_id")` and implement:

```python
from segpick.models import EvidenceAssessment

@register_channel("example")
def assess_example(candidate, recommendation) -> EvidenceAssessment:
    ...
```

The dashboard and JSON report require no channel-specific changes.

## External plug-ins

An external package may expose an assessment builder through a Python entry point:

```toml
[project.entry-points."segpick.evidence_channels"]
example = "segpick_example.channel:assess"
```

SegPick can load installed builders with `discover_external_channels()`.

Discovery does not allow a plug-in to alter ranking. A plug-in assessment must set `participates_in_ranking=False`; future ranking participation will require explicit configuration and a separate scoring adapter.

## Required reproducibility fields

A channel must provide:

- stable channel ID and version;
- score and status;
- confidence level and optional numeric score;
- confidence method name and version;
- confidence factors and limitations;
- a stable finding ID, title, description, severity and priority;
- relevant measurements.
