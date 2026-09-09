from __future__ import annotations

import json
from dataclasses import dataclass

import requests

STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/football/nfl/standings"
USER_AGENT = "curl/8.5.0"  # ESPN 403s a bare/default User-Agent.
REQUEST_TIMEOUT_SECONDS = 15


@dataclass
class Team:
    name: str
    wins: int
    losses: int
    division_wins: int
    division_losses: int
    logo_url: str

    def score(self) -> int:
        return self.wins - self.division_losses


def _logo_url(team_json: dict) -> str:
    logos = team_json.get("logos", [])
    for logo in logos:
        if "default" in logo.get("rel", []):
            return logo["href"]
    return logos[0]["href"] if logos else ""


def _stat_value(stats: list[dict], name: str) -> int:
    for stat in stats:
        if stat["name"] == name:
            return int(stat["value"])
    raise KeyError(f"stat '{name}' not present in ESPN response")


def parse_standings(json_text: str) -> dict[str, Team]:
    data = json.loads(json_text)
    teams: dict[str, Team] = {}
    for conference in data["children"]:
        for entry in conference["standings"]["entries"]:
            team_json = entry["team"]
            stats = entry["stats"]
            name = team_json["displayName"]
            teams[name] = Team(
                name=name,
                wins=_stat_value(stats, "wins"),
                losses=_stat_value(stats, "losses"),
                division_wins=_stat_value(stats, "divisionWins"),
                division_losses=_stat_value(stats, "divisionLosses"),
                logo_url=_logo_url(team_json),
            )
    return teams


def fetch_standings(season: int) -> dict[str, Team]:
    response = requests.get(
        STANDINGS_URL,
        params={"season": season},
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return parse_standings(response.text)
