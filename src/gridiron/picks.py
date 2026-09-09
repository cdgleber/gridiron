from __future__ import annotations

from dataclasses import dataclass

from gridiron.teams import NFL_TEAMS


class PicksValidationError(ValueError):
    pass


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


def validate_picks(betters: list[Better]) -> None:
    """Checks structure and spelling; raises PicksValidationError on the first problem found."""
    names_seen: set[str] = set()
    for better in betters:
        if better.name in names_seen:
            raise PicksValidationError(f"duplicate better name: '{better.name}'")
        names_seen.add(better.name)

        unknown = [pick for pick in better.picks if pick not in NFL_TEAMS]
        if unknown:
            raise PicksValidationError(
                f"better '{better.name}' picked unknown team name(s): {', '.join(unknown)}"
            )

        if len(better.picks) != len(set(better.picks)):
            raise PicksValidationError(f"better '{better.name}' has duplicate picks")

    counts = {better.name: len(better.picks) for better in betters}
    if len(set(counts.values())) > 1:
        detail = ", ".join(f"{name}={count}" for name, count in counts.items())
        raise PicksValidationError(f"betters have differing pick counts: {detail}")
