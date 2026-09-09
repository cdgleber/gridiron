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
