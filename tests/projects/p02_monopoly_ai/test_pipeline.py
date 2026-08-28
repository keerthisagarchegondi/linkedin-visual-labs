"""Scaffold-pipeline tests."""

from linkedin_visual_labs.projects.p02_monopoly_ai.pipeline import (
    validate_scaffold,
)


def test_scaffold_report_matches_contract() -> None:
    report = validate_scaffold()

    assert report.project_id == "p02_monopoly_ai"
    assert report.board_spaces == 40
    assert report.purchasable_assets == 28
    assert report.strategy_count == 4
    assert report.tournament_games == 10000
