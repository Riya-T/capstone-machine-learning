"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with cart.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

from cart import ShoppingCart


def test_undo_reverts_the_last_add():
    cart = ShoppingCart()
    cart.add_item("P1", "Pen", 2.0, 3)
    cart.add_item("P2", "Notebook", 5.0)
    assert cart.undo() is True
    assert cart.get_total() == 6.0


def test_undo_of_remove_restores_removed_quantity():
    cart = ShoppingCart()
    cart.add_item("P1", "Pen", 2.0, 3)
    cart.remove_item("P1", 2)
    assert cart.undo() is True
    assert cart.get_total() == 6.0
