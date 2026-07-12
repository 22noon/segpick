from segpick.config import resolve_config


def test_cli_overrides_yaml_and_yaml_overrides_defaults():
    cfg = resolve_config(
        {"outdir": "yaml_results", "preset": "asm10", "html": True},
        {"outdir": "cli_results", "preset": None, "html": False},
    )
    assert cfg.outdir == "cli_results"
    assert cfg.preset == "asm10"
    assert cfg.html is False
    assert cfg.sample_name == "sample"
