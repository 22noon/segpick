import json
from pathlib import Path

from segpick.analysis.manifest import build_analysis_manifest
from segpick.config import RunConfig
from segpick.models import AnalysisManifest, Sample
from segpick.reasoning import load_active_rules
from segpick.reporting import write_analysis_manifest, write_html_dashboard


def test_build_analysis_manifest_records_active_rules() -> None:
    sample = Sample(name="example")
    candidate_rules, gene_rules = load_active_rules()

    manifest = build_analysis_manifest(
        sample,
        RunConfig(sample_name="example"),
        (*candidate_rules, *gene_rules),
    )

    assert manifest.rule_schema_version == 1
    assert manifest.builtin_rule_count == 6
    assert manifest.user_rule_count == 0
    assert manifest.total_rule_count == 6
    assert manifest.rule_sources == ("builtin:default_rules.yml",)
    assert manifest.gene_count == 0
    assert manifest.hypothesis_count == 0


def test_manifest_is_written_as_json(tmp_path: Path) -> None:
    manifest = AnalysisManifest(
        segpick_version="1.0.0",
        generated_utc="2026-07-26T12:00:00+00:00",
        git_commit="abcdef1234567890",
        rule_schema_version=1,
        builtin_rule_count=3,
        user_rule_count=1,
        rule_sources=("builtin:default_rules.yml", "laboratory.yml"),
        gene_count=10,
        candidate_count=24,
        observation_count=12,
        finding_count=8,
        convergence_count=2,
        hypothesis_count=3,
        recommended_gene_count=10,
        manual_review_count=2,
        resolved_config={"sample_name": "example"},
    )

    path = write_analysis_manifest(manifest, tmp_path / "manifest.json")
    payload = json.loads(path.read_text())

    assert payload["total_rule_count"] == 4
    assert payload["rule_sources"] == [
        "builtin:default_rules.yml",
        "laboratory.yml",
    ]


def test_dashboard_index_shows_manifest(tmp_path: Path) -> None:
    manifest = AnalysisManifest(
        segpick_version="1.0.0",
        generated_utc="2026-07-26T12:00:00+00:00",
        git_commit="abcdef1234567890",
        rule_schema_version=1,
        builtin_rule_count=3,
        user_rule_count=1,
        rule_sources=("builtin:default_rules.yml", "laboratory.yml"),
        gene_count=0,
        candidate_count=0,
        observation_count=12,
        finding_count=8,
        convergence_count=2,
        hypothesis_count=3,
        recommended_gene_count=0,
        manual_review_count=0,
        resolved_config={},
    )

    write_html_dashboard(Sample(name="example"), tmp_path, manifest=manifest)
    html = (tmp_path / "index.html").read_text()

    assert "Analysis provenance" in html
    assert "4 total" in html
    assert "laboratory.yml" in html
    assert "abcdef123456" in html
    assert "12 observations" in html
