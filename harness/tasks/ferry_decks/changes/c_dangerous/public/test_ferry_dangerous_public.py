"""Public checks for the c_dangerous change (dangerous goods on open-air
decks only). Shown to the editor, never to the writer.

Usage (with ferry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_dangerous/public/test_ferry_dangerous_public.py
"""

import pytest
from ferry import Ferry, NotAllowed


@pytest.fixture
def ferry():
    f = Ferry()
    f.add_deck("upper", open_air=True)
    f.add_deck("lower")
    return f


def test_a_dangerous_vehicle_boards_an_open_air_deck(ferry):
    ferry.board("van", "upper")
    ferry.board("tanker", "upper", dangerous=True)
    assert ferry.get_vehicles("upper") == ["van", "tanker"]
    assert ferry.get_dangerous("upper") == ["tanker"]


def test_a_dangerous_vehicle_may_not_board_a_closed_deck(ferry):
    with pytest.raises(NotAllowed):
        ferry.board("tanker", "lower", dangerous=True)
    assert ferry.get_vehicles("lower") == []
    with pytest.raises(KeyError):
        ferry.get_deck_of("tanker")
