"""Public checks for the c_block change (blocked clients). Shown to the
editor, never to the writer.

Usage (with limiter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_block/public/test_block_public.py
"""

import pytest
from limiter import ClientBlocked, RateLimiter


def test_a_blocked_client_cannot_make_requests():
    lim = RateLimiter(window=10)
    lim.add_client("alice", allowance=3)
    lim.block("alice")
    assert lim.is_blocked("alice")
    with pytest.raises(ClientBlocked):
        lim.request("alice")
    lim.unblock("alice")
    assert not lim.is_blocked("alice")
    assert lim.request("alice") == 1


def test_a_blocked_client_has_nothing_remaining():
    lim = RateLimiter(window=10)
    lim.add_client("alice", allowance=3)
    lim.request("alice")
    lim.block("alice")
    assert lim.get_remaining("alice") == 0
    lim.unblock("alice")
    assert lim.get_remaining("alice") == 2
