"""Public checks for the c_plan_version change (versioned subscriptions).
Shown to the editor, never to the writer.

Usage (with billing.py importable, e.g. in the sandbox):
    python -m pytest changes/c_plan_version/public/test_plan_version_public.py
"""

import pytest
from billing import BillingSystem, VersionConflict


def test_a_plan_change_raises_the_version():
    billing = BillingSystem()
    billing.add_plan("basic", 900)
    billing.add_plan("pro", 1500)
    billing.subscribe("alice", "basic")
    assert billing.get_version("alice") == 1
    billing.change_plan("alice", "pro", expected_version=1)
    assert billing.get_version("alice") == 2


def test_a_stale_version_is_refused():
    billing = BillingSystem()
    billing.add_plan("basic", 900)
    billing.add_plan("pro", 1500)
    billing.subscribe("alice", "basic")
    billing.pause("alice")
    with pytest.raises(VersionConflict):
        billing.resume("alice", expected_version=1)
    assert billing.is_paused("alice")
    assert billing.get_version("alice") == 2
