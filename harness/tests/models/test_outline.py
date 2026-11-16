"""Tests for harness.models.outline: the outline the editor sees, SHOW
requests, and splicing complete functions, methods and classes in by name.

Usage:
    uv run pytest tests/models/test_outline.py
"""

import ast

import pytest

from harness.models.outline import (
    FunctionEditError,
    all_names,
    apply_blocks,
    outline_program,
    resolve_names,
    show_requests,
)

SOURCE = '''"""A tiny ledger."""

import json

LIMIT = 100


class LedgerError(Exception):
    pass


class Ledger:
    kind = "plain"

    def __init__(self):
        self._balances = {}

    def deposit(self, account, amount):
        """Add money to an account."""
        self._check(amount)
        self._balances[account] = self._balances.get(account, 0) + amount

    def balance(self, account): return self._balances.get(account, 0)

    def _check(self, amount):
        if amount <= 0:
            raise ValueError(amount)


def dump(ledger):
    return json.dumps(ledger._balances)
'''
FILES = {"ledger.py": SOURCE.encode()}


def text(files):
    return files["ledger.py"].decode()


def apply(code, files=FILES, allowed=("ledger.py",)):
    return apply_blocks(dict(files), [("python file=ledger.py", code)], list(allowed))


# --- the outline ------------------------------------------------------------


def test_outline_hides_bodies_but_keeps_signatures_docstrings_and_attributes():
    out = outline_program(FILES, set())
    assert out.startswith("```python file=ledger.py\n") and out.endswith("```\n")
    assert "LIMIT = 100" in out and 'kind = "plain"' in out and "import json" in out
    assert '    def deposit(self, account, amount):\n        """Add money to an account."""\n' \
        "        ...  # body hidden (SHOW Ledger.deposit)\n" in out  # fmt: skip
    assert "self._check(amount)" not in out
    assert "raise ValueError" not in out
    assert "    ...  # body hidden (SHOW dump)" in out
    # A one-line def has nothing to hide; the exception class body is shown.
    assert "def balance(self, account): return self._balances.get(account, 0)" in out
    assert "class LedgerError(Exception):\n    pass" in out


def test_opened_functions_are_shown_in_full():
    out = outline_program(FILES, {"Ledger._check", "dump"})
    assert "raise ValueError(amount)" in out and "return json.dumps" in out
    assert "(SHOW Ledger.deposit)" in out


def test_a_file_that_does_not_parse_is_shown_whole():
    out = outline_program({"ledger.py": b"def f(:\n    return 1\n"}, set())
    assert "return 1" in out


# --- SHOW -------------------------------------------------------------------


def test_show_lines_are_read_and_names_resolved():
    prose = ["Let me look first.", "SHOW Ledger.deposit, `_check`", "**SHOW**: self.dump()", "x"]
    assert show_requests(prose) == ["Ledger.deposit", "_check", "dump"]
    found, unknown = resolve_names(FILES, ["Ledger.deposit", "_check", "dump", "withdraw"])
    assert found == ["Ledger.deposit", "Ledger._check", "dump"]
    assert unknown == ["withdraw"]
    assert resolve_names(FILES, ["ledger.py:Ledger.balance"]) == (["Ledger.balance"], [])
    assert all_names(FILES) == [
        "Ledger.__init__", "Ledger.deposit", "Ledger.balance", "Ledger._check", "dump",
    ]  # fmt: skip


# --- splicing ---------------------------------------------------------------


def test_a_method_replaces_only_that_method():
    code = (
        "class Ledger:\n    def _check(self, amount):\n"
        "        if amount <= 0 or amount > LIMIT:\n            raise ValueError(amount)\n"
    )
    files, changed, skipped = apply(code)
    assert (changed, skipped) == (["Ledger._check"], [])
    src = text(files)
    assert "amount > LIMIT" in src
    assert src.replace("amount <= 0 or amount > LIMIT", "amount <= 0") == SOURCE
    ast.parse(src)


def test_new_methods_go_at_the_end_of_their_class_and_new_functions_at_the_end():
    code = (
        "class Ledger:\n    def withdraw(self, account, amount):\n        self._check(amount)\n"
        "        self._balances[account] -= amount\n\n"
        "def load(text):\n    return json.loads(text)\n"
    )
    files, changed, _ = apply(code)
    assert changed == ["Ledger.withdraw", "load"]
    tree = ast.parse(text(files))
    ledger = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Ledger")
    assert [f.name for f in ledger.body if isinstance(f, ast.FunctionDef)][-1] == "withdraw"
    assert isinstance(tree.body[-1], ast.FunctionDef) and tree.body[-1].name == "load"


def test_a_new_class_goes_after_its_base_and_imports_and_constants_are_merged():
    code = (
        "import json\nfrom collections import deque\n\nLIMIT = 500\nFEE = 2\n\n"
        "class AccountFrozen(LedgerError):\n    pass\n"
    )
    files, changed, _ = apply(code)
    assert changed == ["AccountFrozen"]
    src = text(files)
    tree = ast.parse(src)
    names = [getattr(n, "name", None) for n in tree.body]
    assert names.index("AccountFrozen") == names.index("LedgerError") + 1
    assert src.count("import json") == 1 and "from collections import deque" in src
    assert "LIMIT = 500" in src and "LIMIT = 100" not in src and "FEE = 2" in src


def test_placeholder_bodies_are_skipped_and_other_statements_too():
    code = (
        "class Ledger:\n"
        '    def deposit(self, account, amount):\n        """Add money."""\n        ...\n\n'
        "    def _check(self, amount):\n        pass\n\n"
        "if __name__ == '__main__':\n    print(1)\n"
    )
    files, changed, skipped = apply(code)
    assert changed == ["Ledger._check"]
    assert skipped[0] == "Ledger.deposit (its body was only `...`)"
    assert skipped[1].startswith("the If statement at line 9")
    src = text(files)
    assert "self._check(amount)" in src  # deposit kept its real body


def test_only_opened_or_fully_shown_functions_can_be_replaced():
    code = (
        "class Ledger:\n"
        "    def _check(self, amount):\n        return None\n\n"
        "    def balance(self, account):\n        return 0\n\n"
        "    def reset(self):\n        self._balances = {}\n"
    )
    blocks = [("python", code)]
    files, changed, skipped = apply_blocks(dict(FILES), blocks, ["ledger.py"], opened=[])
    # _check's body is hidden and was never opened; balance is a one-liner,
    # shown whole; reset is new.
    assert changed == ["Ledger.balance", "Ledger.reset"]
    assert skipped == ["Ledger._check (not opened yet: send SHOW Ledger._check, then change it)"]
    assert "raise ValueError(amount)" in text(files)
    files, changed, skipped = apply_blocks(dict(FILES), blocks, ["ledger.py"], ["Ledger._check"])
    assert (changed, skipped) == (["Ledger._check", "Ledger.balance", "Ledger.reset"], [])


def test_markdown_escapes_and_indented_methods_are_accepted():
    assert show_requests([r"SHOW Ledger.\_\_init\_\_, Ledger.\_check"]) == [
        "Ledger.__init__",
        "Ledger._check",
    ]
    code = "    def _check(self, amount):\n        if amount < 0:\n            raise ValueError\n"
    files, changed, _ = apply(code)
    assert changed == ["Ledger._check"] and "        if amount < 0:" in text(files)


def test_a_method_sent_without_its_class_goes_to_its_class():
    code = "def _check(self, amount):\n    if amount < 0:\n        raise ValueError(amount)\n"
    files, changed, _ = apply(code)
    assert changed == ["Ledger._check"]
    assert "        if amount < 0:" in text(files)
    assert "def _check" not in text(files).split("def dump")[1]


@pytest.mark.parametrize(
    ("code", "allowed", "message"),
    [
        ("def f(:\n    pass\n", ("ledger.py",), "not valid Python"),
        ("def f():\n    return 1\n", ("other.py", "ledger.py"), None),
    ],
)
def test_blocks_that_cannot_apply_raise(code, allowed, message):
    if message is None:  # a block naming a file it may not change
        with pytest.raises(FunctionEditError, match="may not change"):
            apply_blocks(dict(FILES), [("python file=x.py", code)], list(allowed))
        with pytest.raises(FunctionEditError, match="must name its file"):
            apply_blocks(dict(FILES), [("python", code)], list(allowed))
        return
    with pytest.raises(FunctionEditError, match=message):
        apply(code, allowed=allowed)
