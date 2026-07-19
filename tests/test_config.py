from segpick.config import resolve_config
from pathlib import Path


def test_cli_overrides_yaml_and_yaml_overrides_defaults():
    cfg = resolve_config(
        {"outdir": "yaml_results", "preset": "asm10", "html": True},
        {"outdir": "cli_results", "preset": None, "html": False},
    )
    assert cfg.outdir == "cli_results"
    assert cfg.preset == "asm10"
    assert cfg.html is False
    assert cfg.sample_name == "sample"

def test_read_support_yaml_configuration() -> None:
    config = resolve_config(
        {
            "read_support": {
                "depth_dir": "depth",
                "suffix": ".fa.depth.txt",
                "minimum_depth": 5,
                "terminal_fraction": 0.10,
                "minimum_terminal_bases": 25,
                "strict": True,
            }
        },
        {},
    )

    assert config.read_support.depth_dir == Path("depth")
    assert config.read_support.suffix == ".fa.depth.txt"
    assert config.read_support.minimum_depth == 5
    assert config.read_support.terminal_fraction == 0.10
    assert config.read_support.minimum_terminal_bases == 25
    assert config.read_support.strict is True

def test_cli_depth_directory_overrides_yaml() -> None:
    config = resolve_config(
        {
            "read_support": {
                "depth_dir": "yaml_depth",
                "minimum_depth": 3,
            }
        },
        {
            "depth_dir": "cli_depth",
            "minimum_depth": 10,
        },
    )

    assert config.read_support.depth_dir == Path("cli_depth")
    assert config.read_support.minimum_depth == 10
