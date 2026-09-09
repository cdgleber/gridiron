from datetime import datetime, timezone
from pathlib import Path

from gridiron.espn import parse_standings
from gridiron.main import generate_html

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
