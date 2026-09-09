from pathlib import Path

from gridiron.espn import parse_standings

FIXTURE = Path(__file__).parent / "fixtures" / "standings.json"


def test_parses_all_teams_from_both_conferences():
    teams = parse_standings(FIXTURE.read_text())
    assert set(teams) == {
        "Buffalo Bills",
        "Miami Dolphins",
        "Dallas Cowboys",
        "Philadelphia Eagles",
    }


def test_parses_wins_losses_and_division_record():
    teams = parse_standings(FIXTURE.read_text())
    bills = teams["Buffalo Bills"]
    assert bills.wins == 10
    assert bills.losses == 3
    assert bills.division_wins == 4
    assert bills.division_losses == 1
    assert bills.logo_url == "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png"


def test_team_score_is_wins_minus_division_losses():
    teams = parse_standings(FIXTURE.read_text())
    assert teams["Buffalo Bills"].score() == 9  # 10 - 1
    assert teams["Miami Dolphins"].score() == 0  # 4 - 4
    assert teams["Philadelphia Eagles"].score() == 11  # 11 - 0
