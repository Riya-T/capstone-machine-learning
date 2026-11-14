import pytest
from wallet import Wallet


def test_debit_revision_updates_balance_without_touching_other_members():
    wallet = Wallet()
    for member in ("z", "a"):
        wallet.open_member(member)
    wallet.post("initial", "z", "credit", 10)
    wallet.post("other", "a", "credit", 13)
    wallet.post("debit", "z", "debit", 6)
    wallet.post("more", "z", "credit", 5)
    with pytest.raises(ValueError):
        wallet.revise("debit", 12)
    assert wallet.revise("debit", 2) is None
    assert wallet.history("z") == [
        ("initial", "credit", 10),
        ("debit", "debit", 2),
        ("more", "credit", 5),
    ]
    assert wallet.balance("z") == 13
    assert wallet.history("a") == [("other", "credit", 13)]
    with pytest.raises(ValueError):
        wallet.post("debit", "a", "credit", 1)
    wallet.post("spend", "z", "debit", 13)
    assert wallet.balance("z") == 0
