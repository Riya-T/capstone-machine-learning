"""Source measurements are descriptive, deterministic and never execute code.

Usage:
    uv run pytest tests/evaluation/test_source.py
"""

from harness.evaluation.analysis import compare
from harness.evaluation.source import describe_change, describe_source

from .test_analysis import example


def test_counts_only_actual_docstrings_and_unions_overlapping_comment_lines():
    code = b'''"""Module docs."""  # overlaps
x = "not documentation"
def f():
    """Two lines
    of documentation."""
    return "# not a comment"
# actual comment
raise RuntimeError("MUST NEVER EXECUTE")
'''
    metrics = describe_source({"main.py": code, "readme.md": b"# not Python\n"})
    assert metrics == dict(
        source_files=2,
        source_lines=9,
        python_files=1,
        python_lines=8,
        python_syntax_valid=True,
        python_comment_lines=2,
        python_docstring_lines=3,
        python_documentation_lines=4,
        python_documentation_density=0.5,
    )


def test_line_numbers_remain_distinct_across_files_and_encoding_is_respected():
    metrics = describe_source(
        {"a.py": b"# comment\n", "b.py": b"# comment\n", "c.py": b"# coding: latin-1\ns = '\xe9'\n"}
    )
    assert metrics["python_comment_lines"] == 3
    assert metrics["python_syntax_valid"] is True
    assert metrics["python_lines"] == 4


def test_invalid_program_does_not_produce_partially_measured_documentation():
    metrics = describe_source({"a.py": b"# valid\n", "b.py": b"def incomplete(\n"})
    assert metrics["source_lines"] == 2
    assert metrics["python_syntax_valid"] is False
    assert metrics["python_comment_lines"] is None
    assert metrics["python_documentation_density"] is None


def test_no_python_and_empty_python_have_no_density():
    assert describe_source({"readme.md": b"text"})["python_syntax_valid"] is None
    assert describe_source({"empty.py": b""})["python_documentation_density"] is None


def test_source_summary_is_family_weighted_with_explicit_missingness():
    data = example("candidate")
    data["samples"][0]["source_metrics"] = dict(source_lines=10, python_documentation_density=0.2)
    result = compare([data], bootstrap_samples=20)["methods"]["candidate"]
    fields = result["initial_source_descriptives"]["fields"]
    assert fields["source_lines"]["family_weighted_known_mean"] == 10
    assert fields["source_lines"]["missing_samples"] == 1
    assert fields["python_documentation_density"]["family_weighted_known_mean"] == 0.2
    assert result["metrics"]["change_completion"]["estimate"] == 0.75


def test_edit_size_tracks_added_removed_and_modified_files_without_execution():
    before = {"main.py": b"a=1\nb=2\n", "remove.py": b"gone=1\n", "data.bin": b"x"}
    after = {"main.py": b"a=1\nb=3\nc=4\n", "new.py": b"new=1\n", "data.bin": b"xx"}
    change = describe_change(before, after)
    assert change["files_changed"] == 4
    assert change["files_added"] == change["files_removed"] == 1
    assert change["python_lines_added"] == 3
    assert change["python_lines_removed"] == 2
    assert change["bytes_before"] == sum(map(len, before.values()))


def test_unknown_or_undecodable_source_does_not_become_a_zero_diff():
    assert describe_change(None, {"main.py": b"x=1"}) is None
    change = describe_change({"main.py": b"x=1"}, {"main.py": b"\xff"})
    assert change["files_changed"] == 1
    assert change["python_lines_added"] is None
    assert change["python_lines_removed"] is None


def test_unchanged_files_and_line_ending_only_changes_are_described_separately():
    source = {"main.py": b"x=1\n"}
    assert describe_change(source, source)["files_changed"] == 0
    changed = describe_change(source, {"main.py": b"x=1\r\n"})
    assert changed["files_changed"] == 1
    assert changed["python_lines_added"] == changed["python_lines_removed"] == 0
