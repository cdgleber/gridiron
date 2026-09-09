import pytest

from gridiron.espn import Team
from gridiron.picks import Better
from gridiron.scoring import (
    UnknownTeamError,
    better_division_losses,
    better_games_played,
    better_losses,
    better_score,
    better_wins,
    build_better_rows,
    build_popularity_rows,
    build_team_rows,
)

TEAMS = {
    "Buffalo Bills": Team("Buffalo Bills", 10, 3, 4, 1, "https://example.com/buf.png"),
    "Miami Dolphins": Team("Miami Dolphins", 4, 9, 1, 4, "https://example.com/mia.png"),
    "Dallas Cowboys": Team("Dallas Cowboys", 7, 6, 3, 2, "https://example.com/dal.png"),
    "Philadelphia Eagles": Team("Philadelphia Eagles", 11, 2, 5, 0, "https://example.com/phi.png"),
}

ALICE = Better("Alice", ["Buffalo Bills", "Dallas Cowboys"])
BOB = Better("Bob", ["Miami Dolphins", "Philadelphia Eagles"])


def test_better_wins_sums_picked_teams():
    assert better_wins(ALICE, TEAMS) == 17  # 10 + 7


def test_better_losses_sums_picked_teams():
    assert better_losses(ALICE, TEAMS) == 9  # 3 + 6


def test_better_division_losses_sums_picked_teams():
    assert better_division_losses(ALICE, TEAMS) == 3  # 1 + 2


def test_better_games_played_sums_wins_and_losses():
    assert better_games_played(ALICE, TEAMS) == 26  # 17 + 9


def test_better_score_is_wins_minus_division_losses():
    assert better_score(ALICE, TEAMS) == 14  # 9 + 5
    assert better_score(BOB, TEAMS) == 11  # 0 + 11


def test_unknown_pick_raises_with_better_and_team_name():
    bad = Better("Carol", ["Seattle Seahawks"])
    with pytest.raises(UnknownTeamError, match="Carol.*Seattle Seahawks"):
        better_score(bad, TEAMS)


def test_build_better_rows_sorted_by_score_descending():
    rows = build_better_rows([BOB, ALICE], TEAMS)
    assert [row.name for row in rows] == ["Alice", "Bob"]
    assert rows[0].score == 14
    assert rows[0].wins == 17
    assert rows[0].losses == 9
    assert rows[0].division_losses == 3
    assert rows[0].games_played == 26


def test_build_team_rows_includes_unpicked_teams_and_pickers():
    rows = build_team_rows([ALICE, BOB], TEAMS)
    by_name = {row.name: row for row in rows}
    assert by_name["Buffalo Bills"].pickers == ["Alice"]
    assert by_name["Philadelphia Eagles"].pickers == ["Bob"]
    assert [row.name for row in rows] == sorted(by_name)


def test_build_popularity_rows_sorted_by_pick_count_descending():
    carol = Better("Carol", ["Buffalo Bills"])
    team_rows = build_team_rows([ALICE, BOB, carol], TEAMS)
    rows = build_popularity_rows(team_rows)
    assert rows[0].name == "Buffalo Bills"
    assert rows[0].pick_count == 2
    # remaining teams (1 pick each) come next, alphabetically
    assert [row.name for row in rows[1:]] == ["Dallas Cowboys", "Miami Dolphins", "Philadelphia Eagles"]
    assert all(row.pick_count == 1 for row in rows[1:])
