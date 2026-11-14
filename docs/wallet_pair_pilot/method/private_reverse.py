import pytest
from wallet import Wallet


def test_reversing_a_debit_raises_balance_and_reserves_new_id_globally():
    wallet = Wallet()
    for member in ("z", "a"):
        wallet.open_member(member)
    wallet.post("first", "z", "credit", 10)
    wallet.post("buy", "z", "debit", 6)
    wallet.post("reserved", "a", "credit", 8)
    with pytest.raises(ValueError):
        wallet.reverse("buy", "reserved")
    assert wallet.reverse("buy", "undo") is None
    assert wallet.balance("z") == 10
    assert wallet.history("z")[-1] == ("undo", "credit", 6)
    assert wallet.history("a") == [("reserved", "credit", 8)]
    with pytest.raises(ValueError):
        wallet.post("undo", "a", "credit", 1)
    wallet.post("spend", "z", "debit", 10)
    assert wallet.balance("z") == 0
