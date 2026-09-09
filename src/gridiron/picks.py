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
