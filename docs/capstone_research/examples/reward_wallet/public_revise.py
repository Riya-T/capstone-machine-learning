import pytest
from wallet import Wallet


def test_revision_raises_for_historical_overdraft_and_updates_spendable_credits():
    wallet = Wallet()
    wallet.open_member("lee")
    wallet.post("credit", "lee", "credit", 10)
    wallet.post("spend", "lee", "debit", 8)
    wallet.post("reserve", "lee", "credit", 5)
    with pytest.raises(ValueError):
        wallet.revise("credit", 7)
    with pytest.raises(ValueError):
        wallet.revise([], 12)
    assert wallet.history("lee")[0] == ("credit", "credit", 10)
    assert wallet.revise("credit", 12) is None
    wallet.post("spend_again", "lee", "debit", 9)
    assert wallet.balance("lee") == 0
