"""Public checks for the c_denominations change (configuration). Shown to the
editor, never to the writer.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest changes/c_denominations/public/test_denominations_public.py
"""

import pytest
from vaults import Vaults


def test_the_standard_denominations_are_the_default():
    assert Vaults().get_accepted() == [1, 2, 5, 10, 20, 50, 100, 200]


def test_other_denominations_can_be_configured():
    v = Vaults(denominations=[25, 1, 10, 5])
    assert v.get_accepted() == [1, 5, 10, 25]
    v.add_vault("till")
    v.deposit("till", 25, 4)
    assert v.get_count("till", 25) == 4
    with pytest.raises(ValueError):
        v.deposit("till", 50, 1)
