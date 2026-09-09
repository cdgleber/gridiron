from pathlib import Path

import pytest

from gridiron.picks import Better, PicksValidationError, parse_picks, validate_picks

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


def test_validate_picks_accepts_well_formed_input():
    betters = [
        Better(name="Alice", picks=["Buffalo Bills", "Dallas Cowboys"]),
        Better(name="Bob", picks=["Miami Dolphins", "Philadelphia Eagles"]),
    ]
    validate_picks(betters)  # does not raise


def test_validate_picks_rejects_misspelled_team_name():
    betters = [Better(name="Alice", picks=["Buffalo Bils"])]
    with pytest.raises(PicksValidationError, match="unknown team name"):
        validate_picks(betters)


def test_validate_picks_rejects_duplicate_better_names():
    betters = [
        Better(name="Alice", picks=["Buffalo Bills"]),
        Better(name="Alice", picks=["Dallas Cowboys"]),
    ]
    with pytest.raises(PicksValidationError, match="duplicate better name"):
        validate_picks(betters)


def test_validate_picks_rejects_duplicate_picks_within_a_better():
    betters = [Better(name="Alice", picks=["Buffalo Bills", "Buffalo Bills"])]
    with pytest.raises(PicksValidationError, match="duplicate picks"):
        validate_picks(betters)


def test_validate_picks_rejects_uneven_pick_counts():
    betters = [
        Better(name="Alice", picks=["Buffalo Bills", "Dallas Cowboys"]),
        Better(name="Bob", picks=["Miami Dolphins"]),
    ]
    with pytest.raises(PicksValidationError, match="differing pick counts"):
        validate_picks(betters)
