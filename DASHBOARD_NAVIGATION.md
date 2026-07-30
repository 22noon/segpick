# Dashboard navigation

SegPick gene pages are organised into five task-oriented tabs:

- **Summary** — the recommended candidate, confidence, major strengths, conflicts, and comparison with the runner-up.
- **Evidence** — channel assessments and evidence tables.
- **Biological reasoning** — cross-evidence findings, scenarios, and hypotheses.
- **Plots** — coverage, dot plots, structural comparisons, and protein coordinate maps.
- **Details** — rule diagnostics, downloads, and raw candidate sequence.

The recommended candidate is selected initially. The candidate switcher remains above the tab content and updates all candidate-specific panels. Tabs are implemented in the static HTML output and do not require a server. URL fragments such as `#tab-reasoning` can open a particular section directly.

This milestone changes presentation only. It does not change evidence calculation, ranking, scenarios, hypotheses, or recommendations.
