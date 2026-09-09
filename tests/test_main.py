import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from gridiron.espn import parse_standings
from gridiron.main import generate_html, run
from gridiron.picks import PicksValidationError

FIXTURE = Path(__file__).parent / "fixtures" / "standings.json"


def test_generate_html_scores_picks_against_teams():
    teams = parse_standings(FIXTURE.read_text())
    picks_text = "Alice\nBuffalo Bills\nDallas Cowboys\n"
    html = generate_html(
        picks_text,
        teams,
        season=2026,
        generated_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
    )
    assert "Alice" in html
    assert "<td>14</td>" in html  # (10-1) + (7-2)


def test_generate_html_rejects_misspelled_team_name():
    teams = parse_standings(FIXTURE.read_text())
    picks_text = "Alice\nBuffalo Bils\n"
    with pytest.raises(PicksValidationError):
        generate_html(
            picks_text,
            teams,
            season=2026,
            generated_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        )


def test_run_validates_picks_before_fetching_standings(tmp_path, monkeypatch):
    def fail_if_called(season):
        raise AssertionError("fetch_standings should not be called for invalid picks")

    monkeypatch.setattr(sys.modules["gridiron.main"], "fetch_standings", fail_if_called)

    picks_path = tmp_path / "picks.txt"
    picks_path.write_text("Alice\nBuffalo Bils\n")

    with pytest.raises(PicksValidationError):
        run(season=2026, picks_path=picks_path, output_path=tmp_path / "index.html")
