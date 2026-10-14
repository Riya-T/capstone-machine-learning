"""Unit tests for pipeline.parser: accepted answers (prose ignored, exact
bytes, CRLF, long fences), truncation vs malformed categories, every
malformed reason, the real 7B answer in tests/data, and a render/parse round
trip.

Usage:
    uv run pytest tests/test_parser.py
"""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pipeline.parser import ParseFailure, parse_program, render_program

DATA = Path(__file__).parent / "data"
ONE = ["records.py"]
TWO = ["records.py", "storage.py"]


def ok(text, allowed=ONE, finish_reason="stop"):
    result = parse_program(text, allowed, finish_reason)
    assert result.ok, result.failure
    return result.files


def failure(text, allowed=ONE, finish_reason="stop") -> ParseFailure:
    result = parse_program(text, allowed, finish_reason)
    assert not result.ok and result.files is None
    return result.failure


# --- accepted answers -------------------------------------------------------


def test_single_block():
    assert ok("```python file=records.py\nx = 1\n```\n") == {"records.py": b"x = 1\n"}


def test_prose_outside_blocks_is_ignored():
    text = "Here is the code:\n\n```python file=records.py\nx = 1\n```\n\nHope this helps!"
    assert ok(text) == {"records.py": b"x = 1\n"}


def test_several_files_in_any_order():
    text = "```python file=storage.py\ns = 2\n```\nand\n```python file=records.py\nr = 1\n```"
    assert ok(text, TWO) == {"records.py": b"r = 1\n", "storage.py": b"s = 2\n"}


def test_contents_are_preserved_exactly():
    body = 'a = "\\t tab"\n\tindented\nb = "é ∑ 😀"\nc = "\x0c form feed"\nd = " "\n\n\n'
    assert ok(f"```python file=records.py\n{body}```")["records.py"] == body.encode("utf-8")


def test_crlf_answers_keep_their_line_endings():
    text = "```python file=records.py\r\nx = 1\r\ny = 2\r\n```\r\n"
    assert ok(text) == {"records.py": b"x = 1\r\ny = 2\r\n"}


def test_empty_block_is_an_empty_file():
    assert ok("```python file=records.py\n```") == {"records.py": b""}


def test_longer_fence_allows_triple_backticks_inside():
    body = 'DOC = """\n```\nexample\n```\n"""\n'
    assert ok(f"````python file=records.py\n{body}````\n")["records.py"] == body.encode()


def test_unknown_finish_reason_is_not_truncation():
    assert ok("```python file=records.py\nx = 1\n```", finish_reason=None)


def test_real_7b_answer_parses():
    text = (DATA / "qwen7b_record_store_answer.md").read_text(encoding="utf-8")
    files = ok(text)
    assert list(files) == ["records.py"]
    assert files["records.py"].startswith(b"import json\n")
    assert files["records.py"].endswith(b"        return sorted(self.records.keys())\n")


# --- truncation -------------------------------------------------------------


def test_finish_reason_length_is_truncated_even_if_it_parses():
    f = failure("```python file=records.py\nx = 1\n```", finish_reason="length")
    assert (f.category, f.reason) == ("truncated", "max_tokens")


def test_truncated_and_malformed_are_separate_categories():
    cut = failure("```python file=records.py\nx = ", finish_reason="length")
    broken = failure("```python file=records.py\nx = ", finish_reason="stop")
    assert (cut.category, cut.reason) == ("truncated", "max_tokens")
    assert (broken.category, broken.reason) == ("malformed", "unclosed_block")


# --- malformed answers ------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "allowed", "reason"),
    [
        ("Sorry, I can't help with that.", ONE, "no_code"),
        ("", ONE, "no_code"),
        ("```python file=records.py\nx = 1\n", ONE, "unclosed_block"),
        ("```python\nx = 1\n```", ONE, "unlabeled_block"),
        ("```\nx = 1\n```", ONE, "unlabeled_block"),
        # A correct block plus an unlabeled example: ambiguous, so rejected.
        (
            "```python file=records.py\nx = 1\n```\n```python\nrecords.x\n```",
            ONE,
            "unlabeled_block",
        ),
        ("```py file=records.py\nx = 1\n```", ONE, "bad_label"),
        ("```python file=records.py extra\nx = 1\n```", ONE, "bad_label"),
        ("```python  file=records.py\nx = 1\n```", ONE, "bad_label"),
        ('```python file="records.py"\nx = 1\n```', ONE, "bad_path"),
        ("```python file=/tmp/records.py\nx = 1\n```", ONE, "bad_path"),
        ("```python file=../records.py\nx = 1\n```", ONE, "bad_path"),
        ("```python file=pkg\\records.py\nx = 1\n```", ONE, "bad_path"),
        ("```python file=./records.py\nx = 1\n```", ONE, "bad_path"),
        ("```python file=pkg//records.py\nx = 1\n```", ONE, "bad_path"),
        ("```python file=record.py\nx = 1\n```", ONE, "not_allowed"),
        ("```python file=Records.py\nx = 1\n```", ONE, "not_allowed"),
        (
            "```python file=records.py\nx = 1\n```\n```python file=records.py\nx = 2\n```",
            ONE,
            "duplicate",
        ),
        ("```python file=records.py\nr = 1\n```", TWO, "missing_file"),
        # A forgotten closing fence swallows the next block's label into the
        # first file; the second file is then missing, not silently merged.
        (
            "```python file=records.py\nr = 1\n```python file=storage.py\ns = 2\n```",
            TWO,
            "missing_file",
        ),
    ],
)
def test_malformed_answers(text, allowed, reason):
    f = failure(text, allowed)
    assert (f.category, f.reason) == ("malformed", reason)


def test_failure_detail_points_at_the_line():
    f = failure("intro\n\n```python file=other.py\nx\n```")
    assert str(f) == "malformed/not_allowed: line 3: 'other.py' is not one of ['records.py']"


# --- round trip -------------------------------------------------------------

# Lines that don't start with a backtick can never be mistaken for a fence.
line = st.text(st.characters(blacklist_categories=("Cs",), blacklist_characters="\n"), max_size=30)
safe_line = line.filter(lambda s: not s.startswith("`"))
content = st.lists(safe_line, max_size=8).map(lambda lines: "".join(f"{x}\n" for x in lines))


@given(st.dictionaries(st.sampled_from(TWO), content.map(str.encode), min_size=2))
def test_render_then_parse_returns_the_same_bytes(files):
    assert parse_program(render_program(files), TWO, "stop").files == files
