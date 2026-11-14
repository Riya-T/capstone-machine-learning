import pytest
from wallet import Wallet


def test_reverse_uses_existing_history_and_updates_spendable_credits():
    wallet = Wallet()
    wallet.open_member("lee")
    wallet.post("credit", "lee", "credit", 7)
    wallet.post("reserve", "lee", "credit", 3)
    with pytest.raises(ValueError):
        wallet.reverse([], "undo")
    assert wallet.reverse("credit", "undo") is None
    assert wallet.history("lee")[-1] == ("undo", "debit", 7)
    wallet.post("spend", "lee", "debit", 3)
    assert wallet.balance("lee") == 0
