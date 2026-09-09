"""Validates the real picks.txt at the repo root, not a fixture."""

from __future__ import annotations

from pathlib import Path

from gridiron.picks import parse_picks, validate_picks

PICKS_PATH = Path(__file__).parent.parent / "picks.txt"


def test_picks_file_is_valid():
    betters = parse_picks(PICKS_PATH.read_text())
    assert betters
    validate_picks(betters)  # raises PicksValidationError on any problem
