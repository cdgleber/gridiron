from __future__ import annotations

from dataclasses import dataclass

from gridiron.espn import Team
from gridiron.picks import Better


class UnknownTeamError(KeyError):
    pass


def _team_for_pick(better: Better, pick: str, teams: dict[str, Team]) -> Team:
    try:
        return teams[pick]
    except KeyError:
        raise UnknownTeamError(
            f"better '{better.name}' picked unknown team '{pick}'"
        ) from None


def better_wins(better: Better, teams: dict[str, Team]) -> int:
    return sum(_team_for_pick(better, pick, teams).wins for pick in better.picks)


def better_losses(better: Better, teams: dict[str, Team]) -> int:
    return sum(_team_for_pick(better, pick, teams).losses for pick in better.picks)


def better_division_losses(better: Better, teams: dict[str, Team]) -> int:
    return sum(
        _team_for_pick(better, pick, teams).division_losses for pick in better.picks
    )


def better_games_played(better: Better, teams: dict[str, Team]) -> int:
    return better_wins(better, teams) + better_losses(better, teams)


def better_score(better: Better, teams: dict[str, Team]) -> int:
    return sum(_team_for_pick(better, pick, teams).score() for pick in better.picks)


@dataclass
class BetterRow:
    name: str
    score: int
    wins: int
    losses: int
    division_losses: int
    games_played: int


@dataclass
class TeamRow:
    name: str
    logo_url: str
    score: int
    wins: int
    losses: int
    division_losses: int
    games_played: int
    pickers: list[str]


def build_better_rows(betters: list[Better], teams: dict[str, Team]) -> list[BetterRow]:
    rows = [
        BetterRow(
            name=better.name,
            score=better_score(better, teams),
            wins=better_wins(better, teams),
            losses=better_losses(better, teams),
            division_losses=better_division_losses(better, teams),
            games_played=better_games_played(better, teams),
        )
        for better in betters
    ]
    rows.sort(key=lambda row: (-row.score, row.name))
    return rows


def build_team_rows(betters: list[Better], teams: dict[str, Team]) -> list[TeamRow]:
    pickers_by_team: dict[str, list[str]] = {name: [] for name in teams}
    for better in betters:
        for pick in better.picks:
            _team_for_pick(better, pick, teams)  # validates the pick up front
            pickers_by_team[pick].append(better.name)

    rows = [
        TeamRow(
            name=team.name,
            logo_url=team.logo_url,
            score=team.score(),
            wins=team.wins,
            losses=team.losses,
            division_losses=team.division_losses,
            games_played=team.wins + team.losses,
            pickers=sorted(pickers_by_team[team.name]),
        )
        for team in teams.values()
    ]
    rows.sort(key=lambda row: row.name)
    return rows
