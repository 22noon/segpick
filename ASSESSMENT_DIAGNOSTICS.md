# Assessment Diagnostics

SegPick evidence channels may attach `AssessmentDiagnostics` to explain whether
prerequisites were available and why an assessment stopped. Each `DiagnosticCheck`
records a stable identifier, title, status (`pass`, `warn`, `fail`, or `not_run`),
a human-readable detail, and an optional value.

The dashboard shows diagnostics when a channel is not assessable or a check fails.
The same structure is exported under `diagnostics` in each evidence assessment's
JSON representation.

Junction Read Support v1.1 is the first fully instrumented channel. It reports:

- reference dot-plot availability;
- usable reference alignment blocks;
- per-base depth-profile availability;
- unsupported internal sequence reported by Reference Compatibility;
- assessable interval construction;
- a specific stop reason.

Diagnostics explain missing inference; they do not alter ranking.
