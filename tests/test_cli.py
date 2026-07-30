from segpick.cli import build_parser


def test_html_option_is_available_on_run_subcommand():
    parser = build_parser()
    args = parser.parse_args(
        [
            "run",
            "--hits",
            "hits.tsv",
            "--contigs",
            "contigs.fa",
            "--refs",
            "refs.fa",
            "--html",
        ]
    )
    assert args.command == "run"
    assert args.html is True

def test_run_parser_accepts_depth_directory() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "run",
            "--hits",
            "hits.tsv",
            "--contigs",
            "contigs.fa",
            "--refs",
            "refs.fa",
            "--depth-dir",
            "depth",
            "--depth-suffix",
            ".fa.depth.txt",
            "--minimum-depth",
            "5",
        ]
    )

    assert args.depth_dir == "depth"
    assert args.depth_suffix == ".fa.depth.txt"
    assert args.minimum_depth == 5
