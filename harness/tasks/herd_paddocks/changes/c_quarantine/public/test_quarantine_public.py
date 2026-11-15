"""Public checks for the c_quarantine change (quarantined paddocks). Shown to
the editor, never to the writer.

Usage (with farm.py importable, e.g. in the sandbox):
    python -m pytest changes/c_quarantine/public/test_quarantine_public.py
"""

import pytest
from farm import Farm, Quarantined


@pytest.fixture
def farm():
    f = Farm()
    f.add_paddock("north")
    f.arrive("north", "sheep", 5)
    return f


def test_no_animal_arrives_in_a_quarantined_paddock(farm):
    farm.quarantine("north")
    with pytest.raises(Quarantined):
        farm.arrive("north", "sheep", 1)
    assert farm.get_count("north", "sheep") == 5
    farm.release("north")
    farm.arrive("north", "sheep", 1)
    assert farm.get_count("north", "sheep") == 6


def test_no_animal_departs_from_a_quarantined_paddock(farm):
    farm.quarantine("north")
    with pytest.raises(Quarantined):
        farm.depart("north", "sheep", 2)
    assert farm.get_count("north", "sheep") == 5
