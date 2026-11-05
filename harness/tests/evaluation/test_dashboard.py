"""Offline dashboard labels, safe escaping and complete accounting from saved records.

Usage:
    uv run pytest tests/evaluation/test_dashboard.py
"""

import shutil
import subprocess
from html.parser import HTMLParser

import pytest

from harness.evaluation.analysis import compare
from harness.evaluation.dashboard import SCRIPT, render_dashboard
from harness.evaluation.integrity import verify_report
from harness.evaluation.report import write_report

from .test_analysis import example


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.nodes = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


def result():
    return compare([example(), example("candidate")], bootstrap_samples=20)


def test_dashboard_is_self_contained_accessible_and_has_all_accounting_rows():
    html = render_dashboard(result())
    page = Page(html)
    assert "SYNTHETIC FIXTURE" in html
    assert "+50.0 pp" in html
    assert "not independent evidence" in html
    assert sum(attrs.get("data-kind") == "checkpoint" for _, attrs in page.nodes) == 48
    assert sum(attrs.get("data-kind") == "stop" for _, attrs in page.nodes) == 13
    ids = {a["id"] for _, a in page.nodes if "id" in a}
    assert {"method", "status", "query", "reset", "filter-count", "filters"} <= ids
    assert len(ids) == sum("id" in a for _, a in page.nodes)
    assert not any("src" in attrs for _, attrs in page.nodes)
    assert not any(tag == "link" for tag, _ in page.nodes)
    assert not any(
        a.get("href", "").startswith(("http", "file:", "javascript:")) for _, a in page.nodes
    )
    assert any(a.get("http-equiv") == "Content-Security-Policy" for _, a in page.nodes)
    assert any(a.get("aria-live") == "polite" for _, a in page.nodes)


def test_record_content_cannot_inject_html_or_script_and_private_metadata_is_not_embedded():
    data = example("candidate")
    data["provenance"] = {"private_path": "NEVER_SHOW_THIS_PRIVATE_PATH"}
    trial = data["samples"][0]["trials"][0]
    trial["steps"][1].update(status="fail_new", end_reason='</script><img src="https://evil">')
    comparison = compare([data], bootstrap_samples=20)
    comparison["notes"].append('<script>alert("unsafe")</script>')
    html = render_dashboard(comparison)
    page = Page(html)
    assert not any(tag == "img" for tag, _ in page.nodes)
    assert sum(tag == "script" for tag, _ in page.nodes) == 1
    assert "&lt;/script&gt;&lt;img" in html
    assert "NEVER_SHOW_THIS_PRIVATE_PATH" not in html


def test_single_method_missing_work_displays_unknown_without_inventing_a_win():
    data = example("candidate")
    data["samples"][0]["trials"][0]["steps"] = []
    html = render_dashboard(compare([data], bootstrap_samples=20))
    assert "unavailable" in html
    assert "not_reached_after_missing" in html
    assert 'data-status="missing"' in html
    assert "+50.0 pp" not in html


def test_html_is_deterministic_included_in_manifest_and_verified(tmp_path):
    comparison = result()
    paths = write_report(comparison, tmp_path)
    assert paths["report.html"].read_text(encoding="utf8") == render_dashboard(comparison)
    assert "report.html" in verify_report(tmp_path)["files_verified"]
    first = paths["report.html"].read_bytes()
    write_report(comparison, tmp_path)
    assert paths["report.html"].read_bytes() == first


def test_filter_script_on_mock_elements_without_a_browser():
    """Exercise display filtering only; this is not a rendered-browser test."""
    node = shutil.which("node")
    if node is None:
        pytest.skip(
            "Optional JavaScript logic check requires installed Node; no runtime dependency"
        )
    before = r"""
const assert = require('node:assert/strict');
const ids = ['method', 'status', 'query', 'reset', 'filter-count', 'filters'];
const controls = Object.fromEntries(ids
  .map(id => [id, {value:'', hidden:true, events:{}, textContent:'',
    addEventListener(kind, fn) { this.events[kind] = fn; }}]));
const fixtures = [
 {dataset:{method:'original', status:'success', kind:'checkpoint'}, textContent:'original alpha'},
 {dataset:{method:'candidate', status:'fail_new', kind:'checkpoint'}, textContent:'candidate beta'},
 {dataset:{method:'candidate', status:'fail_new', kind:'stop'}, textContent:'candidate beta'},
];
const document = { getElementById(id) {return controls[id];},
 querySelectorAll(selector) {assert.equal(selector, 'tr[data-method]'); return fixtures;} };
"""
    after = r"""
assert.equal(controls.filters.hidden, false);
assert.ok(controls['filter-count'].textContent.startsWith('2 checkpoint rows and 1 stop rows'));
controls.method.value = 'candidate'; controls.method.events.input();
assert.deepEqual(fixtures.map(r => r.hidden), [true, false, false]);
controls.status.value = 'success'; controls.status.events.input();
assert.ok(fixtures.every(r => r.hidden));
controls.reset.events.click();
assert.ok(fixtures.every(r => !r.hidden));
controls.query.value = '  BETA  '; controls.query.events.input();
assert.deepEqual(fixtures.map(r => r.hidden), [true, false, false]);
assert.ok(controls['filter-count'].textContent.endsWith('Summary scores stay unchanged.'));
"""
    process = subprocess.run(
        [node, "-e", before + SCRIPT + after], capture_output=True, text=True, timeout=15
    )
    assert process.returncode == 0, process.stderr
