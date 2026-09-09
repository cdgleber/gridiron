# NFL Pool Standings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI (`uv run gridiron`) that fetches current NFL standings from ESPN, scores each pool participant's picked teams (`wins − divisional losses`, summed), and writes a static `index.html` leaderboard — plus the GitHub Actions workflow and docs to run it on a schedule and host it on GitHub Pages.

**Architecture:** A small pipeline of pure, independently-testable modules under `src/gridiron/`: `espn.py` (fetch + parse ESPN's standings JSON into `Team` objects), `picks.py` (parse the pool's `picks.txt` into `Better` objects), `scoring.py` (pure scoring functions + row-builders for the template), `render.py` (Jinja2 template → HTML string), `main.py` (CLI glue: fetch, parse, score, render, write file). No database, no server — the only side effects are one HTTP GET and one file write.

**Tech Stack:** Python 3.14, `uv` for dependency/project management, `requests` for HTTP, `jinja2` for templating, `pytest` for tests.

**Spec:** `docs/superpowers/specs/2026-09-08-nfl-pool-standings-design.md`

## Global Constraints

- ESPN standings endpoint: `https://site.api.espn.com/apis/v2/sports/football/nfl/standings?season={year}` — one request returns all 32 teams' `wins`, `losses`, `divisionWins`, `divisionLosses`.
- Requests to ESPN must set `User-Agent: curl/8.5.0` (a bare/default UA gets a 403).
- Team score = `wins − division_losses`. A better's score = sum of their picked teams' scores.
- A pick in `picks.txt` with no matching ESPN team name must raise an error that names both the better and the unmatched pick — never silently skip it.
- No live network calls in the test suite — all tests run against fixture JSON/text.
- `index.html` is committed to the repo and served directly by GitHub Pages from `main` — no build step at request time.

---

### Task 1: Project dependencies

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `requests`, `jinja2` available as runtime imports; `pytest` available for `uv run pytest`.

- [ ] **Step 1: Add runtime dependencies**

Run: `uv add requests jinja2`

- [ ] **Step 2: Add dev dependency**

Run: `uv add --dev pytest`

- [ ] **Step 3: Verify the environment resolves**

Run: `uv sync`
Expected: completes with no errors; `uv.lock` is created/updated.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add requests, jinja2, pytest dependencies"
```

---

### Task 2: ESPN standings fetch + parse

**Files:**
- Create: `src/gridiron/espn.py`
- Create: `tests/fixtures/standings.json`
- Test: `tests/test_espn.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass
  class Team:
      name: str
      wins: int
      losses: int
      division_wins: int
      division_losses: int
      logo_url: str

      def score(self) -> int: ...

  def parse_standings(json_text: str) -> dict[str, Team]: ...
  def fetch_standings(season: int) -> dict[str, Team]: ...
  ```
  `parse_standings` keys the dict by `Team.name` (ESPN's `displayName`, e.g. `"Buffalo Bills"`) — this is the join key `picks.txt` entries must match exactly.

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/standings.json` (a trimmed real ESPN response shape — two conferences, two teams each):

```json
{
  "children": [
    {
      "name": "American Football Conference",
      "standings": {
        "entries": [
          {
            "team": {
              "displayName": "Buffalo Bills",
              "logos": [
                {"href": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png", "rel": ["full", "default"]}
              ]
            },
            "stats": [
              {"name": "wins", "value": 10.0, "displayValue": "10"},
              {"name": "losses", "value": 3.0, "displayValue": "3"},
              {"name": "divisionWins", "value": 4.0, "displayValue": "4"},
              {"name": "divisionLosses", "value": 1.0, "displayValue": "1"}
            ]
          },
          {
            "team": {
              "displayName": "Miami Dolphins",
              "logos": [
                {"href": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png", "rel": ["full", "default"]}
              ]
            },
            "stats": [
              {"name": "wins", "value": 4.0, "displayValue": "4"},
              {"name": "losses", "value": 9.0, "displayValue": "9"},
              {"name": "divisionWins", "value": 1.0, "displayValue": "1"},
              {"name": "divisionLosses", "value": 4.0, "displayValue": "4"}
            ]
          }
        ]
      }
    },
    {
      "name": "National Football Conference",
      "standings": {
        "entries": [
          {
            "team": {
              "displayName": "Dallas Cowboys",
              "logos": [
                {"href": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png", "rel": ["full", "default"]}
              ]
            },
            "stats": [
              {"name": "wins", "value": 7.0, "displayValue": "7"},
              {"name": "losses", "value": 6.0, "displayValue": "6"},
              {"name": "divisionWins", "value": 3.0, "displayValue": "3"},
              {"name": "divisionLosses", "value": 2.0, "displayValue": "2"}
            ]
          },
          {
            "team": {
              "displayName": "Philadelphia Eagles",
              "logos": [
                {"href": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png", "rel": ["full", "default"]}
              ]
            },
            "stats": [
              {"name": "wins", "value": 11.0, "displayValue": "11"},
              {"name": "losses", "value": 2.0, "displayValue": "2"},
              {"name": "divisionWins", "value": 5.0, "displayValue": "5"},
              {"name": "divisionLosses", "value": 0.0, "displayValue": "0"}
            ]
          }
        ]
      }
    }
  ]
}
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_espn.py`:

```python
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_espn.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gridiron.espn'`

- [ ] **Step 4: Implement `espn.py`**

Create `src/gridiron/espn.py`:

```python
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_espn.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add src/gridiron/espn.py tests/test_espn.py tests/fixtures/standings.json
git commit -m "feat: fetch and parse ESPN NFL standings"
```

---

### Task 3: Picks file parsing

**Files:**
- Create: `src/gridiron/picks.py`
- Create: `tests/fixtures/picks.txt`
- Test: `tests/test_picks.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass
  class Better:
      name: str
      picks: list[str]

  def parse_picks(text: str) -> list[Better]: ...
  ```

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/picks.txt`:

```
Alice
Buffalo Bills
Dallas Cowboys

Bob
Miami Dolphins
Philadelphia Eagles
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_picks.py`:

```python
from pathlib import Path

from gridiron.picks import parse_picks

FIXTURE = Path(__file__).parent / "fixtures" / "picks.txt"


def test_parses_each_better_and_their_picks():
    betters = parse_picks(FIXTURE.read_text())
    assert len(betters) == 2
    alice, bob = betters
    assert alice.name == "Alice"
    assert alice.picks == ["Buffalo Bills", "Dallas Cowboys"]
    assert bob.name == "Bob"
    assert bob.picks == ["Miami Dolphins", "Philadelphia Eagles"]


def test_strips_trailing_whitespace_and_carriage_returns():
    text = "Alice\r\nBuffalo Bills \r\nDallas Cowboys\r\n"
    betters = parse_picks(text)
    assert betters == [type(betters[0])(name="Alice", picks=["Buffalo Bills", "Dallas Cowboys"])]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_picks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gridiron.picks'`

- [ ] **Step 4: Implement `picks.py`**

Create `src/gridiron/picks.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Better:
    name: str
    picks: list[str]


def parse_picks(text: str) -> list[Better]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [block for block in normalized.split("\n\n") if block.strip()]

    betters: list[Better] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        name, *picks = lines
        betters.append(Better(name=name, picks=picks))
    return betters
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_picks.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add src/gridiron/picks.py tests/test_picks.py tests/fixtures/picks.txt
git commit -m "feat: parse pool picks from picks.txt"
```

---

### Task 4: Scoring and row-building

**Files:**
- Create: `src/gridiron/scoring.py`
- Test: `tests/test_scoring.py`

**Interfaces:**
- Consumes: `Team` (`src/gridiron/espn.py`), `Better` (`src/gridiron/picks.py`)
- Produces:
  ```python
  class UnknownTeamError(KeyError): ...

  def better_wins(better: Better, teams: dict[str, Team]) -> int: ...
  def better_losses(better: Better, teams: dict[str, Team]) -> int: ...
  def better_division_losses(better: Better, teams: dict[str, Team]) -> int: ...
  def better_games_played(better: Better, teams: dict[str, Team]) -> int: ...
  def better_score(better: Better, teams: dict[str, Team]) -> int: ...

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

  def build_better_rows(betters: list[Better], teams: dict[str, Team]) -> list[BetterRow]: ...
  def build_team_rows(betters: list[Better], teams: dict[str, Team]) -> list[TeamRow]: ...
  ```
  `build_better_rows` is sorted by `score` descending (ties broken by `name` ascending). `build_team_rows` is sorted by `name` ascending and covers every team in `teams`, including ones nobody picked (`pickers == []`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_scoring.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scoring.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gridiron.scoring'`

- [ ] **Step 3: Implement `scoring.py`**

Create `src/gridiron/scoring.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_scoring.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/gridiron/scoring.py tests/test_scoring.py
git commit -m "feat: score betters and build leaderboard/team rows"
```

---

### Task 5: HTML rendering

**Files:**
- Create: `src/gridiron/render.py`
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: `BetterRow`, `TeamRow` (`src/gridiron/scoring.py`)
- Produces:
  ```python
  def render_page(
      better_rows: list[BetterRow],
      team_rows: list[TeamRow],
      season: int,
      generated_at: datetime,
  ) -> str: ...
  ```

- [ ] **Step 1: Write the failing test**

Create `tests/test_render.py`:

```python
from datetime import datetime, timezone

from gridiron.render import render_page
from gridiron.scoring import BetterRow, TeamRow

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

GENERATED_AT = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def test_renders_better_names_and_scores():
    html = render_page(BETTER_ROWS, TEAM_ROWS, season=2026, generated_at=GENERATED_AT)
    assert "Alice" in html
    assert "<td>14</td>" in html
    assert "Bob" in html
    assert "<td>11</td>" in html


def test_renders_team_logo_and_pickers():
    html = render_page(BETTER_ROWS, TEAM_ROWS, season=2026, generated_at=GENERATED_AT)
    assert 'src="https://example.com/buf.png"' in html
    assert "Alice" in html  # listed as a picker of the Bills


def test_renders_season_and_updated_timestamp():
    html = render_page(BETTER_ROWS, TEAM_ROWS, season=2026, generated_at=GENERATED_AT)
    assert "2026" in html
    assert "2026-09-08 12:00:00 UTC" in html


def test_escapes_html_in_better_names():
    rows = [BetterRow(name="<script>", score=0, wins=0, losses=0, division_losses=0, games_played=0)]
    html = render_page(rows, [], season=2026, generated_at=GENERATED_AT)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_render.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gridiron.render'`

- [ ] **Step 3: Implement `render.py`**

Create `src/gridiron/render.py`:

```python
from __future__ import annotations

from datetime import datetime

from jinja2 import Environment

from gridiron.scoring import BetterRow, TeamRow

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NFL Pool Standings</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f172a; color: #e2e8f0; padding: 24px; }
  .container { max-width: 1100px; margin: 0 auto; }
  h1 { font-size: 1.8rem; margin-bottom: 4px; }
  .updated { color: #94a3b8; font-size: 0.85rem; margin-bottom: 24px; }
  .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 24px; }
  h2 { font-size: 1.2rem; margin-bottom: 12px; }
  input.search { padding: 8px 14px; border-radius: 8px; border: 1px solid #334155;
                 background: #0f172a; color: #e2e8f0; margin-bottom: 12px; width: 100%; max-width: 320px; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; padding: 10px; cursor: pointer; background: #334155;
       position: sticky; top: 0; }
  th:first-child { border-top-left-radius: 8px; }
  th:last-child { border-top-right-radius: 8px; }
  td { padding: 10px; border-bottom: 1px solid #334155; }
  img.logo { max-width: 28px; height: auto; }
  .better-link { color: #38bdf8; cursor: pointer; }
  .better-link:hover { text-decoration: underline; }
  .active-filter { color: #f472b6; font-weight: 700; }
</style>
</head>
<body>
<div class="container">
  <h1>NFL Pool Standings</h1>
  <div class="updated">Season {{ season }} &middot; Updated: {{ generated_at }}</div>

  <div class="card">
    <h2>Leaderboard</h2>
    <input class="search" id="searchBetters" placeholder="Search betters...">
    <table id="betters">
      <thead>
        <tr>
          <th onclick="sortTable('betters', 0)">Better</th>
          <th onclick="sortTable('betters', 1)">Score</th>
          <th onclick="sortTable('betters', 2)">Wins</th>
          <th onclick="sortTable('betters', 3)">Losses</th>
          <th onclick="sortTable('betters', 4)">Div Losses</th>
          <th onclick="sortTable('betters', 5)">Games Played</th>
        </tr>
      </thead>
      <tbody>
        {% for row in better_rows %}
        <tr>
          <td>{{ row.name }}</td>
          <td>{{ row.score }}</td>
          <td>{{ row.wins }}</td>
          <td>{{ row.losses }}</td>
          <td>{{ row.division_losses }}</td>
          <td>{{ row.games_played }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Teams</h2>
    <input class="search" id="searchTeams" placeholder="Search teams...">
    <table id="teams">
      <thead>
        <tr>
          <th></th>
          <th onclick="sortTable('teams', 1)">Team</th>
          <th onclick="sortTable('teams', 2)">Score</th>
          <th onclick="sortTable('teams', 3)">Wins</th>
          <th onclick="sortTable('teams', 4)">Losses</th>
          <th onclick="sortTable('teams', 5)">Div Losses</th>
          <th onclick="sortTable('teams', 6)">Games Played</th>
          <th>Betters</th>
        </tr>
      </thead>
      <tbody>
        {% for row in team_rows %}
        <tr>
          <td><img class="logo" src="{{ row.logo_url }}" alt=""></td>
          <td>{{ row.name }}</td>
          <td>{{ row.score }}</td>
          <td>{{ row.wins }}</td>
          <td>{{ row.losses }}</td>
          <td>{{ row.division_losses }}</td>
          <td>{{ row.games_played }}</td>
          <td>
            {% for picker in row.pickers %}<span class="better-link" onclick="filterByBetter('{{ picker }}')">{{ picker }}</span>{% if not loop.last %}, {% endif %}{% endfor %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
function sortTable(tableId, columnIndex) {
  const table = document.getElementById(tableId);
  const rows = Array.from(table.tBodies[0].rows);
  const numeric = columnIndex > 0;
  const current = table.dataset.sortCol === String(columnIndex) ? table.dataset.sortDir : "desc";
  const dir = current === "asc" ? "desc" : "asc";
  rows.sort((a, b) => {
    let x = a.cells[columnIndex].innerText.trim();
    let y = b.cells[columnIndex].innerText.trim();
    if (numeric) { x = parseFloat(x) || 0; y = parseFloat(y) || 0; }
    if (x < y) return dir === "asc" ? -1 : 1;
    if (x > y) return dir === "asc" ? 1 : -1;
    return 0;
  });
  rows.forEach(row => table.tBodies[0].appendChild(row));
  table.dataset.sortCol = String(columnIndex);
  table.dataset.sortDir = dir;
}

function filterByBetter(name) {
  const rows = document.getElementById("teams").tBodies[0].rows;
  for (const row of rows) {
    row.style.display = row.cells[7].innerText.includes(name) ? "" : "none";
  }
  document.querySelectorAll(".better-link").forEach(el => {
    el.classList.toggle("active-filter", el.textContent === name);
  });
}

function wireSearch(inputId, tableId, columnIndex) {
  document.getElementById(inputId).addEventListener("input", (e) => {
    const filter = e.target.value.toLowerCase();
    const rows = document.getElementById(tableId).tBodies[0].rows;
    for (const row of rows) {
      const text = row.cells[columnIndex].innerText.toLowerCase();
      row.style.display = text.includes(filter) ? "" : "none";
    }
  });
}

wireSearch("searchBetters", "betters", 0);
wireSearch("searchTeams", "teams", 1);
</script>
</body>
</html>
"""

_env = Environment(autoescape=True)
_template = _env.from_string(_TEMPLATE)


def render_page(
    better_rows: list[BetterRow],
    team_rows: list[TeamRow],
    season: int,
    generated_at: datetime,
) -> str:
    return _template.render(
        better_rows=better_rows,
        team_rows=team_rows,
        season=season,
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_render.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/gridiron/render.py tests/test_render.py
git commit -m "feat: render standings leaderboard as static HTML"
```

---

### Task 6: CLI entry point

**Files:**
- Create: `src/gridiron/main.py`
- Modify: `src/gridiron/__init__.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `fetch_standings`/`parse_standings`/`Team` (`espn.py`), `parse_picks`/`Better` (`picks.py`), `build_better_rows`/`build_team_rows` (`scoring.py`), `render_page` (`render.py`)
- Produces:
  ```python
  def generate_html(picks_text: str, teams: dict[str, Team], season: int, generated_at: datetime) -> str: ...
  def run(season: int, picks_path: Path, output_path: Path) -> None: ...
  def main() -> None: ...
  ```
  `main` is the console-script target (`pyproject.toml`'s `gridiron = "gridiron:main"`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_main.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gridiron.main'`

- [ ] **Step 3: Implement `main.py`**

Create `src/gridiron/main.py`:

```python
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from gridiron.espn import Team, fetch_standings
from gridiron.picks import parse_picks
from gridiron.render import render_page
from gridiron.scoring import build_better_rows, build_team_rows


def generate_html(
    picks_text: str,
    teams: dict[str, Team],
    season: int,
    generated_at: datetime,
) -> str:
    betters = parse_picks(picks_text)
    better_rows = build_better_rows(betters, teams)
    team_rows = build_team_rows(betters, teams)
    return render_page(better_rows, team_rows, season, generated_at)


def run(season: int, picks_path: Path, output_path: Path) -> None:
    picks_text = picks_path.read_text()
    teams = fetch_standings(season)
    html = generate_html(picks_text, teams, season, datetime.now(timezone.utc))
    output_path.write_text(html)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the NFL pool standings page.")
    parser.add_argument("--season", type=int, default=datetime.now().year)
    parser.add_argument("--picks", type=Path, default=Path("picks.txt"))
    parser.add_argument("--output", type=Path, default=Path("index.html"))
    args = parser.parse_args()
    run(args.season, args.picks, args.output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Wire up the package entry point**

Modify `src/gridiron/__init__.py` (currently empty) to:

```python
from gridiron.main import main

__all__ = ["main"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_main.py -v`
Expected: PASS (1 test)

- [ ] **Step 6: Run the full test suite**

Run: `uv run pytest -v`
Expected: all tests across `tests/test_espn.py`, `tests/test_picks.py`, `tests/test_scoring.py`, `tests/test_render.py`, `tests/test_main.py` PASS.

- [ ] **Step 7: Commit**

```bash
git add src/gridiron/main.py src/gridiron/__init__.py tests/test_main.py
git commit -m "feat: wire up gridiron CLI entry point"
```

---

### Task 7: Sample picks file, README, and GitHub Actions workflow

**Files:**
- Create: `picks.txt`
- Create: `README.md` (overwrite existing placeholder)
- Create: `.github/workflows/update-standings.yml`

**Interfaces:**
- Consumes: `gridiron` console script (Task 6) via `uv run gridiron`.
- Produces: `index.html` at repo root (generated, not hand-written); a scheduled workflow that regenerates and commits it.

- [ ] **Step 1: Create a starter `picks.txt`**

Create `picks.txt` at the repo root (placeholder pool — replace with real picks before each season's draft):

```
Alice
Buffalo Bills
Kansas City Chiefs
Philadelphia Eagles
San Francisco 49ers

Bob
Dallas Cowboys
Baltimore Ravens
Detroit Lions
Green Bay Packers
```

- [ ] **Step 2: Generate the page locally and verify it**

Run: `uv run gridiron`
Expected: exits 0; `index.html` is created at the repo root; open it (or `grep -o '<title>[^<]*' index.html`) and confirm it contains `Alice`, `Bob`, and real, current win/loss numbers for the picked teams.

- [ ] **Step 3: Write the README**

Replace the contents of `README.md`:

```markdown
# Gridiron — NFL Pool Standings

A static leaderboard for a "pick your teams" NFL pool. Each participant
picks a set of NFL teams; a team scores `wins − divisional losses`; a
participant's score is the sum across their picks. Standings come from
ESPN's public API — no RapidAPI key, no database, no server.

## How scoring works

For each team: `score = wins - divisional_losses`.
For each better: `score = sum(team.score() for team in their picks)`.

## Setting up a new season's pool

Edit `picks.txt` at the repo root. Format: a better's name on one line,
followed by one NFL team name per line (must exactly match ESPN's team
name, e.g. `Buffalo Bills`, not `Bills`), with a blank line between
betters:

```
Alice
Buffalo Bills
Kansas City Chiefs

Bob
Dallas Cowboys
Baltimore Ravens
```

## Running it locally

```bash
uv run gridiron                       # writes index.html for the current year
uv run gridiron --season 2025         # override the season
uv run gridiron --picks other.txt     # use a different picks file
```

Requires `picks.txt` to only contain team names ESPN recognizes — an
unknown pick raises an error naming the better and the bad team name
instead of silently dropping it.

## Running the tests

```bash
uv run pytest
```

## Automatic updates

`.github/workflows/update-standings.yml` runs `uv run gridiron` on a
schedule (Tuesday mornings, after Monday Night Football) and on manual
trigger, committing `index.html` back to `main` when it changes.

## Hosting on GitHub Pages

1. Push this repo to GitHub.
2. In the repo, go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to `Deploy from a
   branch`, branch `main`, folder `/ (root)`. Save.
4. Your page is live at `https://<username>.github.io/<repo>/` within a
   few minutes.

## Using your own domain

1. Buy/own a domain (or use a subdomain of one you already have, e.g.
   `standings.example.com`).
2. Add a `CNAME` file to the repo root containing just your domain, e.g.:
   ```
   standings.example.com
   ```
   (GitHub Pages regenerates this automatically once you set the custom
   domain in the UI in step 4 below — you can also create it yourself.)
3. At your DNS provider, create a record pointing at GitHub Pages:
   - **Subdomain** (e.g. `standings.example.com`): a `CNAME` record
     pointing to `<username>.github.io`.
   - **Apex/root domain** (e.g. `example.com`): four `A` records
     pointing at GitHub Pages' IPs:
     ```
     185.199.108.153
     185.199.109.153
     185.199.110.153
     185.199.111.153
     ```
     (Some providers offer `ALIAS`/`ANAME` records instead of `A` records
     for apex domains — use those if available.)
4. Back in **Settings → Pages**, enter your custom domain under
   **Custom domain** and save. Optionally check **Enforce HTTPS** once
   GitHub provisions a certificate (can take up to 24 hours after DNS
   propagates).
5. DNS changes can take anywhere from a few minutes to 48 hours to
   propagate; GitHub's Pages settings page will show a green check once
   it can verify your domain.
```

- [ ] **Step 4: Write the GitHub Actions workflow**

Create `.github/workflows/update-standings.yml`:

```yaml
name: Update standings

on:
  schedule:
    - cron: "0 11 * * 2"  # Tuesday 11:00 UTC, after Monday Night Football
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Generate standings page
        run: uv run gridiron

      - name: Commit if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add index.html
          git diff --cached --quiet || git commit -m "chore: update standings"
          git push
```

- [ ] **Step 5: Validate the workflow YAML parses**

Run: `python3 -c "import yaml, sys; yaml.safe_load(open('.github/workflows/update-standings.yml')); print('ok')"`
Expected: prints `ok` (install with `uv run --with pyyaml python3 -c "..."` if `yaml` isn't available system-wide)

- [ ] **Step 6: Commit**

```bash
git add picks.txt README.md .github/workflows/update-standings.yml index.html
git commit -m "docs: add README, sample picks, and scheduled GitHub Actions workflow"
```

---

## Self-Review Notes

- **Spec coverage:** ESPN fetch/parse (Task 2), picks parsing (Task 3), scoring incl. fail-fast on unknown picks (Task 4), HTML render reusing the CRGA_Football-style sortable/searchable/filterable UI (Task 5), CLI orchestration with `--season` override (Task 6), sample `picks.txt` + README (pool setup, local run, Pages enablement, custom-domain DNS) + scheduled Actions workflow with `workflow_dispatch` (Task 7) — every spec section has a task.
- **Placeholder scan:** no TBD/TODO; all code blocks are complete and runnable as written.
- **Type consistency:** `Team` (espn.py) → consumed by `scoring.py` and `main.py` with matching field names (`wins`, `losses`, `division_wins`, `division_losses`, `logo_url`, `score()`). `Better` (picks.py) → consumed by `scoring.py`/`main.py` as `name`/`picks`. `BetterRow`/`TeamRow` (scoring.py) → consumed by `render.py` with matching field names throughout.
