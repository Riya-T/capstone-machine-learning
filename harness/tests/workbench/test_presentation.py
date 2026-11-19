"""Check readable report HTML without accepting script or raw HTML input.

Usage: python -m pytest tests/workbench/test_presentation.py
"""

from harness.workbench.presentation import render_report_text


def test_tables_lists_headings_and_inline_commands_are_rendered():
    text = "# Report\n\n| Method | Rate |\n|---|---:|\n| base | 50% |\n\n- Missing stays missing.\n\nRun `verify` now."
    rendered = render_report_text(text)
    assert "<h1>Report</h1>" in rendered
    assert "<th>Method</th>" in rendered and "<td>50%</td>" in rendered
    assert "<li>Missing stays missing.</li>" in rendered
    assert "<code>verify</code>" in rendered
    assert "|---|" not in rendered


def test_raw_html_scripts_and_script_inside_code_are_inert():
    text = "<script>alert('x')</script>\n\n`</code><img src=x onerror=alert(1)>`"
    rendered = render_report_text(text)
    assert "<script>" not in rendered and "<img" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "<code>&lt;/code&gt;&lt;img" in rendered


def test_missing_table_separator_is_plain_text_not_an_invented_table():
    assert "<table>" not in render_report_text("| Method | Rate |\n| base | 50% |")
