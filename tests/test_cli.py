from segpick.cli import build_parser


def test_html_option_is_available_on_run_subcommand():
    parser = build_parser()
    args = parser.parse_args([
        "run",
        "--hits", "hits.tsv",
        "--contigs", "contigs.fa",
        "--refs", "refs.fa",
        "--html",
    ])
    assert args.command == "run"
    assert args.html is True
