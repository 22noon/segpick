# Reasoning Graph Inspector

This milestone exposes the Reasoning Engine V3 graph in the Expert tab without changing ranking or biological behaviour.

For each selected candidate the inspector reports:

- measurement, observation, interpretation and hypothesis node counts;
- graph validation status;
- built-in and plugin evidence sources;
- hypothesis provenance paths;
- a formatted graph JSON preview;
- a downloadable per-candidate reasoning graph JSON file.

Plugin evidence sources retain their `plugin:<channel_id>` namespace throughout the graph and are displayed separately from built-in sources.
