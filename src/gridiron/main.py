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


def _default_season(now: datetime) -> int:
    return now.year - 1 if now.month < 3 else now.year


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the NFL pool standings page.")
    parser.add_argument("--season", type=int, default=_default_season(datetime.now(timezone.utc)))
    parser.add_argument("--picks", type=Path, default=Path("picks.txt"))
    parser.add_argument("--output", type=Path, default=Path("index.html"))
    args = parser.parse_args()
    run(args.season, args.picks, args.output)


if __name__ == "__main__":
    main()
