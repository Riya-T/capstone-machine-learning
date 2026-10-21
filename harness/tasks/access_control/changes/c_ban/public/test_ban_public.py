"""Public checks for the c_ban change (banned clients). Shown to the editor,
never to the writer.

Usage (with gateway.py importable, e.g. in the sandbox):
    python -m pytest changes/c_ban/public/test_ban_public.py
"""

import pytest
from gateway import ClientBanned, Gateway


def test_a_banned_client_leaves_the_allow_list_and_cannot_send():
    gw = Gateway()
    gw.register("alpha")
    gw.allow("alpha")
    gw.ban("alpha")
    assert gw.is_banned("alpha")
    assert gw.get_banned() == ["alpha"]
    assert gw.get_allowed() == []
    with pytest.raises(ClientBanned):
        gw.send("alpha", "hello")
    with pytest.raises(ClientBanned):
        gw.allow("alpha")


def test_unbanning_does_not_restore_access_by_itself():
    gw = Gateway()
    gw.register("alpha")
    gw.allow("alpha")
    gw.ban("alpha")
    gw.unban("alpha")
    assert not gw.is_banned("alpha")
    assert gw.get_allowed() == []
    gw.allow("alpha")
    gw.send("alpha", "hello")
    assert gw.get_messages("alpha") == ["hello"]
