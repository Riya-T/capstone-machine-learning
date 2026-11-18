"""Public checks for the c_seal change (state_flag). Shown to the editor,
never to the writer.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest changes/c_seal/public/test_seal_public.py
"""

import pytest
from silos import SiloSealed, Silos


@pytest.fixture
def silos():
    s = Silos()
    s.add_silo("north")
    s.add_silo("south")
    s.load("north", "wheat", 30)
    return s


def test_sealed_silos_are_listed(silos):
    assert silos.get_sealed() == []
    silos.seal("north")
    assert silos.get_sealed() == ["north"]


def test_no_grain_enters_a_sealed_silo(silos):
    silos.seal("north")
    with pytest.raises(SiloSealed):
        silos.load("north", "wheat", 5)
    assert silos.get_tonnes("north", "wheat") == 30


def test_unseal_lifts_the_seal(silos):
    silos.seal("north")
    silos.unseal("north")
    silos.unload("north", "wheat", 10)
    assert silos.get_tonnes("north", "wheat") == 20
    assert silos.get_sealed() == []
