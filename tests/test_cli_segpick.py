from segpick.cli import build_parser


def test_run_subcommand_and_config_option_exist():
    parser = build_parser()
    args = parser.parse_args(["run", "--config", "config.yml", "--html"])
    assert args.command == "run"
    assert args.config == "config.yml"
    assert args.html is True
