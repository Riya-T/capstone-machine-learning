"""Tests for harness.models.patch: reading SEARCH/REPLACE edits (file names,
fences, markers), applying them in order, skipping the ones that don't
match or repeat an earlier edit, and every failure reason.

Usage:
    uv run pytest tests/models/test_patch.py
"""

import pytest

from harness.models.patch import EditError, apply_edits, split_edits

ONE = ["records.py"]
TWO = ["records.py", "storage.py"]
FILES = {
    "records.py": b"class Store:\n    def get(self, key):\n        return self._data[key]\n\n"
    b"    def put(self, key, value):\n        self._data[key] = value\n",
    "storage.py": b"def load(path):\n    return {}\n",
}
GET = "    def get(self, key):\n        return self._data[key]\n"
NEW_GET = "    def get(self, key, default=None):\n        return self._data.get(key, default)\n"


def edit(search, replace, name="records.py"):
    head = f"{name}\n" if name else ""
    return f"{head}<<<<<<< SEARCH\n{search}=======\n{replace}>>>>>>> REPLACE\n"


def applied(text, allowed=ONE, files=None):
    """The files after the reply's edits, which must all apply."""
    edits, _ = split_edits(text, allowed)
    result = apply_edits(dict(files or FILES), edits)
    assert not result.failures, result.failures
    return result.files


def reason(text, allowed=ONE, files=None) -> str:
    """Why the reply, or its only edit, is refused."""
    try:
        edits, _ = split_edits(text, allowed)
    except EditError as exc:
        return exc.reason
    ((_, error),) = apply_edits(dict(files or FILES), edits).failures
    return error.reason


# --- accepted edits ---------------------------------------------------------


def test_an_edit_replaces_exactly_the_quoted_lines():
    out = applied("Here is the change.\n\n" + edit(GET, NEW_GET) + "\nRUN_CHECKS\n")
    assert out["records.py"] == FILES["records.py"].replace(GET.encode(), NEW_GET.encode())
    assert out["storage.py"] == FILES["storage.py"]


def test_the_file_name_may_be_left_out_when_one_file_may_change():
    assert applied(edit(GET, NEW_GET, name=None)) == applied(edit(GET, NEW_GET))


@pytest.mark.parametrize(
    "wrap",
    [
        lambda e: f"```python\n{e}```\n",  # name inside a ```python block
        lambda e: f"```\n{e}```\n",
        lambda e: "```python file=records.py\n" + e.split("\n", 1)[1] + "```\n",  # label
        lambda e: "**records.py**\n" + e.split("\n", 1)[1],  # markdown around the name
        lambda e: "`records.py`:\n\n" + e.split("\n", 1)[1],
        lambda e: "records.py\n```python\n" + e.split("\n", 1)[1] + "```\n",  # name above
    ],
)
def test_edits_inside_or_outside_fences_name_their_file(wrap):
    out = applied(wrap(edit(GET, NEW_GET)), allowed=TWO)
    assert NEW_GET.encode() in out["records.py"]


def test_edits_apply_in_order_and_later_edits_see_earlier_ones():
    text = edit(GET, NEW_GET) + edit(NEW_GET, "    def get(self, key):\n        return 1\n")
    assert b"return 1" in applied(text)["records.py"]


def test_edits_to_two_files():
    text = edit(GET, NEW_GET) + edit("    return {}\n", "    return {'a': 1}\n", "storage.py")
    out = applied(text, allowed=TWO)
    assert NEW_GET.encode() in out["records.py"] and b"'a': 1" in out["storage.py"]


def test_an_empty_replace_deletes_the_lines():
    put = "\n    def put(self, key, value):\n        self._data[key] = value\n"
    assert applied(edit(put, ""))["records.py"] == b"class Store:\n" + GET.encode()


def test_trailing_whitespace_is_ignored_only_when_nothing_matches_exactly():
    out = applied(edit("    def get(self, key):   \n        return self._data[key]\n", NEW_GET))
    assert NEW_GET.encode() in out["records.py"]


def test_crlf_replies_work():
    out = applied(edit(GET, NEW_GET).replace("\n", "\r\n"))
    assert out["records.py"] == FILES["records.py"].replace(GET.encode(), NEW_GET.encode())


def test_the_final_newline_is_kept():
    files = {"records.py": b"x = 1\n"}
    assert applied(edit("x = 1\n", "x = 2\n"), files=files) == {"records.py": b"x = 2\n"}


def test_lines_outside_edits_are_returned_for_commands():
    text = edit(GET, "    def get(self, key):\nDONE\n") + "\nRUN_CHECKS\n"
    _, outside = split_edits(text, ONE)
    assert "RUN_CHECKS" in outside and "DONE" not in outside


def test_no_edits_is_not_an_error():
    assert split_edits("RUN_CHECKS\n", ONE) == ([], ["RUN_CHECKS", ""])


# --- failures ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "allowed", "expected"),
    [
        ("records.py\n<<<<<<< SEARCH\nx\n>>>>>>> REPLACE\n", ONE, "unclosed_edit"),
        ("records.py\n<<<<<<< SEARCH\nx\n=======\ny\n", ONE, "unclosed_edit"),
        ("<<<<<<< SEARCH\nx\n=======\n<<<<<<< SEARCH\n", ONE, "unclosed_edit"),
        (edit("", NEW_GET), ONE, "empty_search"),
        (edit(GET, NEW_GET, name=None), TWO, "no_file"),  # two files may change
        (edit(GET, NEW_GET, name="tests/test_records.py"), ONE, "not_allowed"),
        (edit("    def missing(self):\n", NEW_GET), ONE, "new_code"),
        (edit("    x = self._data\n", NEW_GET), ONE, "not_found"),
        (edit("    return {}\n", ""), TWO, "not_found"),  # a storage.py line
        ("```python file=records.py\nx = 1\n```\nRUN_CHECKS\n", ONE, "whole_file"),
    ],
)
def test_failure_reasons(text, allowed, expected):
    assert reason(text, allowed) == expected


def test_search_lines_that_match_twice_are_ambiguous():
    files = {"records.py": b"x = 1\ny = 2\nx = 1\n"}
    assert reason(edit("x = 1\n", "x = 3\n"), files=files) == "ambiguous"
    # Quoting one more line makes it unique.
    out = applied(edit("y = 2\nx = 1\n", "y = 2\nx = 3\n"), files=files)
    assert out == {"records.py": b"x = 1\ny = 2\nx = 3\n"}


def test_a_failing_edit_is_skipped_and_the_others_apply():
    files = dict(FILES)
    put = "        self._data[key] = value\n"
    text = edit(GET, NEW_GET) + edit("    def missing(self):\n", "") + edit(put, put + "x\n")
    edits, _ = split_edits(text, ONE)
    result = apply_edits(files, edits)
    assert files == FILES  # the input is never changed
    assert (result.applied, result.repeated, len(result.failures)) == (2, 0, 1)
    ((number, error),) = result.failures
    assert number == 2 and str(error).startswith("edit 2 (records.py, line 10 of your reply)")
    assert NEW_GET.encode() in result.files["records.py"]
    assert result.files["records.py"].endswith(b"value\nx\n")


def test_an_edit_repeating_an_earlier_one_is_skipped_silently():
    # The second edit quotes the old lines, which the first already replaced.
    edits, _ = split_edits(edit(GET, NEW_GET) + edit(GET, NEW_GET), ONE)
    result = apply_edits(FILES, edits)
    assert (result.applied, result.repeated, result.failures) == (1, 1, [])
    assert result.files["records.py"].count(NEW_GET.encode()) == 1


def test_an_edit_that_changes_nothing_does_not_count_as_applied():
    edits, _ = split_edits(edit(GET, GET) + edit(GET, NEW_GET), ONE)
    result = apply_edits(FILES, edits)
    assert (result.applied, result.unchanged, result.failures) == (1, 1, [])


def test_quoting_a_method_the_file_does_not_have_yet_says_how_to_add_one():
    new = "    def size(self):\n        return len(self._data)\n"
    edits, _ = split_edits(edit(new, new + "\n    def clear(self):\n        pass\n"), ONE)
    ((_, error),) = apply_edits(FILES, edits).failures
    assert error.reason == "new_code"
    assert "start with `def size(self):`, which is not in the current file yet" in str(error)
    # A def the file has, quoted wrongly, is an ordinary mismatch.
    edits, _ = split_edits(edit("    def get(self, key):\n        pass\n", ""), ONE)
    assert apply_edits(FILES, edits).failures[0][1].reason == "not_found"


def test_fence_lines_copied_into_an_edit_are_dropped():
    out = applied(edit(f"```python\n{GET}```\n", f"```python\n{NEW_GET}```\n"))
    assert out["records.py"] == FILES["records.py"].replace(GET.encode(), NEW_GET.encode())


def test_messages_say_what_to_fix():
    with pytest.raises(EditError, match=r"put the file name \(records.py, storage.py\)"):
        split_edits(edit(GET, NEW_GET, name=None), TWO)
    edits, _ = split_edits(edit("x = 1\n", ""), ONE)
    ((_, error),) = apply_edits({"records.py": b"x = 1\nx = 1\n"}, edits).failures
    assert "match 2 places" in str(error)
