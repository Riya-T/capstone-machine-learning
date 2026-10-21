"""Public checks for the c_counts change (message statistics). Shown to the
editor, never to the writer.

Usage (with gateway.py importable, e.g. in the sandbox):
    python -m pytest changes/c_counts/public/test_counts_public.py
"""

from gateway import Gateway


def test_counts_for_one_client():
    gw = Gateway()
    gw.register("alpha")
    gw.allow("alpha")
    gw.send("alpha", "hi")
    gw.send("alpha", "hello")
    assert gw.get_message_count("alpha") == 2
    assert gw.get_character_count("alpha") == 7
    assert gw.get_total_messages() == 2


def test_ranking_includes_silent_clients():
    gw = Gateway()
    for name in ["alpha", "bravo", "charlie"]:
        gw.register(name)
        gw.allow(name)
    gw.send("bravo", "one")
    gw.send("bravo", "two")
    gw.send("charlie", "three")
    assert gw.get_ranking() == [("bravo", 2), ("charlie", 1), ("alpha", 0)]
