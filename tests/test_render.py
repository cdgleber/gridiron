from datetime import datetime, timezone

from gridiron.render import render_page
from gridiron.scoring import BetterRow, TeamRow, build_popularity_rows

BETTER_ROWS = [
    BetterRow(name="Alice", score=14, wins=17, losses=9, division_losses=3, games_played=26),
    BetterRow(name="Bob", score=11, wins=15, losses=11, division_losses=4, games_played=26),
]

TEAM_ROWS = [
    TeamRow(
        name="Buffalo Bills",
        logo_url="https://example.com/buf.png",
        score=9,
        wins=10,
        losses=3,
        division_losses=1,
        games_played=13,
        pickers=["Alice"],
    ),
    TeamRow(
        name="Miami Dolphins",
        logo_url="https://example.com/mia.png",
        score=0,
        wins=4,
        losses=9,
        division_losses=4,
        games_played=13,
        pickers=[],
    ),
]

POPULARITY_ROWS = build_popularity_rows(TEAM_ROWS)

GENERATED_AT = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def test_renders_better_names_and_scores():
    html = render_page(BETTER_ROWS, TEAM_ROWS, POPULARITY_ROWS, season=2026, generated_at=GENERATED_AT)
    assert "Alice" in html
    assert "<td>14</td>" in html
    assert "Bob" in html
    assert "<td>11</td>" in html


def test_renders_team_logo_and_pickers():
    html = render_page(BETTER_ROWS, TEAM_ROWS, POPULARITY_ROWS, season=2026, generated_at=GENERATED_AT)
    assert 'src="https://example.com/buf.png"' in html
    assert "Alice" in html  # listed as a picker of the Bills


def test_renders_season_and_updated_timestamp():
    html = render_page(BETTER_ROWS, TEAM_ROWS, POPULARITY_ROWS, season=2026, generated_at=GENERATED_AT)
    assert "2026" in html
    assert "2026-09-08 08:00:00 EDT" in html


def test_escapes_html_in_better_names():
    rows = [BetterRow(name="<script>", score=0, wins=0, losses=0, division_losses=0, games_played=0)]
    html = render_page(rows, [], [], season=2026, generated_at=GENERATED_AT)
    # The better's name should be escaped in the table row
    assert "<td>&lt;script&gt;</td>" in html
    assert "&lt;script&gt;" in html


def test_renders_team_popularity_counts():
    html = render_page(BETTER_ROWS, TEAM_ROWS, POPULARITY_ROWS, season=2026, generated_at=GENERATED_AT)
    assert "Team Popularity" in html
    # Bills has one picker, Dolphins has none; Bills should be listed first (higher pick count)
    bills_index = html.index("Buffalo Bills", html.index("Team Popularity"))
    dolphins_index = html.index("Miami Dolphins", html.index("Team Popularity"))
    assert bills_index < dolphins_index
    assert "<td>1</td>" in html
