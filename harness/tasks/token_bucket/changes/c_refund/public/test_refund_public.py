"""Public checks for the c_refund change (refunding a request). Shown to the
editor, never to the writer.

Usage (with limiter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_refund/public/test_refund_public.py
"""

import pytest
from limiter import LimiterError, RateLimiter


def test_a_refund_gives_the_request_back():
    lim = RateLimiter(window=10)
    lim.add_client("alice", allowance=1)
    receipt = lim.request("alice")
    assert lim.get_remaining("alice") == 0
    lim.refund(receipt)
    assert lim.get_remaining("alice") == 1
    assert lim.get_receipts("alice") == []
    assert lim.request("alice") == 2


def test_a_receipt_can_only_be_refunded_once():
    lim = RateLimiter(window=10)
    lim.add_client("alice", allowance=3)
    lim.request("alice")
    lim.request("alice")
    lim.refund(1)
    with pytest.raises(LimiterError):
        lim.refund(1)
    assert lim.get_receipts("alice") == [2]
    assert lim.get_remaining("alice") == 2


def test_an_unknown_receipt_raises_key_error():
    lim = RateLimiter(window=10)
    lim.add_client("alice", allowance=3)
    with pytest.raises(KeyError):
        lim.refund(1)
