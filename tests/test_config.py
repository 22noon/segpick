from segpick.config import resolve_config
from pathlib import Path

import yaml

from segpick.config import ReadSupportConfig, RunConfig


def test_run_config_to_dict_is_yaml_safe() -> None:
    config = RunConfig(
        hits=Path("hits.tsv"),
        contigs=Path("contigs.fa"),
        refs=Path("refs.fa"),
        outdir=Path("results"),
        read_support=ReadSupportConfig(
            depth_dir=Path("depth"),
        ),
    )

    payload = config.to_dict()

    assert payload["hits"] == "hits.tsv"
    assert payload["outdir"] == "results"
    assert payload["read_support"]["depth_dir"] == "depth"

    # Must not raise a RepresenterError.
    yaml.safe_dump(payload)


def test_cli_overrides_yaml_and_yaml_overrides_defaults():
    cfg = resolve_config(
        {"outdir": "yaml_results", "html": True},
        {"outdir": "cli_results", "html": False},
    )
    assert cfg.outdir == "cli_results"
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


def test_reference_dotplot_cli_overrides_yaml():
    from segpick.config import resolve_config

    config = resolve_config(
        {
            "reference_dotplots": {
                "enabled": False,
                "task": "blastn",
                "evalue": 0.01,
                "word_size": 7,
            }
        },
        {
            "reference_dotplots_enabled": True,
            "reference_dotplot_task": "megablast",
            "reference_dotplot_evalue": 1e-5,
            "reference_dotplot_word_size": None,
            "force_reference_dotplots": True,
        },
    )
    assert config.reference_dotplots.enabled is True
    assert config.reference_dotplots.task == "megablast"
    assert config.reference_dotplots.evalue == 1e-5
    assert config.reference_dotplots.word_size == 7
    assert config.reference_dotplots.force is True


def test_contig_dotplot_cli_overrides_yaml():
    config = resolve_config(
        {
            "contig_dotplots": {
                "enabled": False,
                "task": "blastn",
                "evalue": 0.01,
                "word_size": 7,
            }
        },
        {
            "contig_dotplots_enabled": True,
            "contig_dotplot_task": "megablast",
            "contig_dotplot_evalue": 1e-5,
            "contig_dotplot_word_size": None,
            "force_contig_dotplots": True,
        },
    )
    assert config.contig_dotplots.enabled is True
    assert config.contig_dotplots.task == "megablast"
    assert config.contig_dotplots.evalue == 1e-5
    assert config.contig_dotplots.word_size == 7
    assert config.contig_dotplots.force is True
