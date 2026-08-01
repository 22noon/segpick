from pathlib import Path


def test_cli_uses_distinct_rule_and_final_hypothesis_functions():
    cli_text = (Path(__file__).parents[1] / "segpick" / "cli.py").read_text(encoding="utf-8")

    assert "attach_biological_hypotheses as attach_rule_based_findings" in cli_text
    assert "attach_rule_based_findings(" in cli_text
    assert "candidate_rules=candidate_rules" in cli_text
    assert "attach_biological_hypotheses(sample, candidate_hypotheses, gene_hypotheses)" in cli_text
