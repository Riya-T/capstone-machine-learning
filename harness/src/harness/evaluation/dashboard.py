"""Render an offline, self-contained comparison dashboard from saved outcomes.

Usage:
    html = render_dashboard(comparison)
    # No model calls, external assets, code execution or web server required.
"""

from __future__ import annotations

from html import escape

from .diagnostics import diagnostic_rows

STYLE = """
:root {font:16px/1.5 system-ui,sans-serif;color:#172235;background:#f4f6fa}
* {box-sizing:border-box} body {margin:0} main {max-width:1250px;margin:auto;padding:32px 24px}
h1 {font-size:2rem;line-height:1.2;margin:10px 0} h2 {margin:0 0 12px;font-size:1.3rem}
p {margin:8px 0} .muted,caption {color:#45556e} .eyebrow {font-weight:700;color:#2458a6}
.notice {padding:14px 18px;background:#fff3cd;border-left:5px solid #946400;margin:20px 0}
.panel {background:white;border:1px solid #d4dce8;border-radius:10px;padding:22px;margin:22px 0}
.scroll {overflow:auto} table {width:100%;border-collapse:collapse;text-align:left;font-size:.9rem}
caption {text-align:left;margin-bottom:12px}
th,td {padding:10px 12px;border-bottom:1px solid #e1e6ef;
vertical-align:top} th {background:#eef2f8} td.number {font-variant-numeric:tabular-nums}
.filters {display:flex;flex-wrap:wrap;gap:16px;margin-bottom:16px;align-items:end}
label {display:grid;gap:5px;font-weight:600} input,select,button {font:inherit;padding:8px;
border:1px solid #8492a8;border-radius:5px;background:white;color:inherit}
button {cursor:pointer} a {color:#174c9b;text-underline-offset:3px} .downloads {display:flex;
flex-wrap:wrap;gap:16px} .badge {display:inline-block;border-radius:4px;padding:2px 6px;
background:#e9eef6;overflow-wrap:anywhere} .success {background:#d8f1e4;color:#155537}
.failure {background:#fde2e1;color:#852422} .unknown {background:#fff1cd;color:#694b00}
code {font-size:.85em;overflow-wrap:anywhere} [hidden] {display:none!important}
:focus-visible {outline:3px solid #4b7bd1;outline-offset:3px}
@media(max-width:600px) {main {padding:16px 10px}.panel {padding:14px}h1 {font-size:1.6rem}}
@media print {.filters,button {display:none}.panel {break-inside:avoid}.scroll {overflow:visible}
main {max-width:none;padding:0}body {background:white}}
"""

SCRIPT = """
const method = document.getElementById('method');
const status = document.getElementById('status');
const query = document.getElementById('query');
const rows = [...document.querySelectorAll('tr[data-method]')];
function applyFilters() {
  let checkpoints = 0, stops = 0;
  const term = query.value.toLowerCase().trim();
  for (const row of rows) {
    const visible = (!method.value || row.dataset.method === method.value) &&
      (!status.value || row.dataset.status === status.value) &&
      (!term || row.textContent.toLowerCase().includes(term));
    row.hidden = !visible;
    if (visible) { if (row.dataset.kind === 'checkpoint') checkpoints++; else stops++; }
  }
  document.getElementById('filter-count').textContent =
    `${checkpoints} checkpoint rows and ${stops} stop rows shown. Summary scores stay unchanged.`;
}
for (const control of [method, status, query]) control.addEventListener('input', applyFilters);
document.getElementById('reset').addEventListener('click', () => {
  method.value = ''; status.value = ''; query.value = ''; applyFilters();
});
document.getElementById('filters').hidden = false;
applyFilters();
"""


def _text(value):
    return "—" if value is None else escape(str(value), quote=True)


def _rate(value):
    return "unavailable" if value is None else f"{value:.1%}"


def _table(headers, rows, caption):
    return (
        f'<div class="scroll"><table><caption>{escape(caption)}</caption><thead><tr>'
        + "".join(f'<th scope="col">{escape(h)}</th>' for h in headers)
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def _status(value):
    category = (
        "success"
        if value == "success"
        else "failure"
        if value.startswith("fail_") or value in ("initial_fail", "initial_parse_failure")
        else "unknown"
    )
    return f'<span class="badge {category}">{_text(value)}</span>'


def _row(values, attributes=""):
    return f"<tr{attributes}>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>"


def render_dashboard(result):
    """HTML-escape all record content; filters affect display, never the analysis."""
    title = {
        "fixture": "SYNTHETIC FIXTURE — not experimental evidence",
        "development": "Development comparison — not held-out evidence",
        "heldout": "Held-out writer comparison",
    }[result["purpose"]]
    checkpoints, failures = diagnostic_rows(result)
    parts = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        "style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; "
        "form-action 'none'\">",
        f"<title>{escape(title)}</title><style>{STYLE}</style></head><body><main>",
        '<header><p class="eyebrow">Writer evaluation</p><h1>Compare modification outcomes</h1>',
        f'<p class="notice">{escape(title)}</p>',
        f"<p>Reference: <strong>{_text(result['reference'])}</strong>. "
        "This page opens offline; it does not contact models or load external assets.</p></header>",
        '<section class="panel"><h2>Overall comparison</h2>',
    ]
    rows = []
    for name, method in result["methods"].items():
        metrics, counts = method["metrics"], method["counts"]
        rows.append(
            _row(
                [
                    _text(name),
                    *[
                        _rate(metrics[key]["estimate"])
                        for key in (
                            "initial_correctness",
                            "change_completion",
                            "change_completion_initially_correct",
                            "whole_sequence_success",
                        )
                    ],
                    f"{counts.get('regressions', 0)} / "
                    f"{counts.get('steps_behaviorally_evaluated', 0)}",
                    str(counts["trajectories_planned"] - counts.get("trajectories_resolved", 0)),
                ]
            )
        )
    parts += [
        _table(
            [
                "Method",
                "Initial tests",
                "Changes / all",
                "Changes / initially passing",
                "Whole sequences / all",
                "Regressions / evaluated",
                "Unresolved trials",
            ],
            rows,
            "Family-weighted rates. Missing outcomes block primary scores; "
            "filtering does not rescore.",
        ),
        '</section><section class="panel"><h2>Difference from reference</h2>',
    ]
    rows = []
    for pair in result["comparisons"]:
        metric = pair["metrics"]["change_completion"]
        interval = metric["interval"]
        rows.append(
            _row(
                [
                    _text(pair["method"]),
                    "unavailable"
                    if metric["difference"] is None
                    else f"{metric['difference'] * 100:+.1f} pp",
                    "unavailable"
                    if interval is None
                    else f"[{interval[0] * 100:+.1f}, {interval[1] * 100:+.1f}] pp",
                    str(metric["paired_families"]),
                ]
            )
        )
    parts += [
        _table(
            ["Method", "Completion difference", "Exploratory interval", "Paired families"],
            rows,
            f"{result['bootstrap']['confidence']:.0%} percentile bootstrap over "
            "task families; repetitions are not independent evidence.",
        ),
        "<p>Positive means more changes completed. It does not establish causation or "
        "a reliable preference label. Initially passing subsets can differ between writers.</p>",
        '</section><section class="panel"><h2>Inspect individual outcomes</h2>',
        "<p>Code failures, budget stops, infrastructure errors, missing work and "
        "not-reached changes remain separate. Stop reasons are recorded metadata, "
        "not verified explanations of code defects.</p>",
        '<div id="filters" class="filters" hidden><label>Method<select id="method">'
        '<option value="">All methods</option>',
    ]
    parts += [f'<option value="{_text(name)}">{_text(name)}</option>' for name in result["methods"]]
    parts += [
        '</select></label><label>Outcome<select id="status"><option value="">All outcomes</option>'
    ]
    statuses = sorted({row["status"] for row in checkpoints + failures})
    parts += [f'<option value="{_text(s)}">{_text(s)}</option>' for s in statuses]
    parts += [
        "</select></label><label>Search task, family, change or reason"
        '<input id="query" type="search"></label><button id="reset" type="button">'
        'Reset filters</button></div><p id="filter-count" role="status" aria-live="polite"></p>',
        "<h3>First stops</h3>",
    ]
    for kind, records, headers in (
        (
            "stop",
            failures,
            [
                "Method",
                "Task / family",
                "Seed",
                "Sequence / repetition",
                "Stage",
                "Change",
                "Outcome",
                "Recorded reason",
            ],
        ),
        (
            "checkpoint",
            checkpoints,
            [
                "Method",
                "Task / family",
                "Seed",
                "Sequence / repetition",
                "Step",
                "Change",
                "Outcome",
                "Recorded reason",
            ],
        ),
    ):
        rows = []
        for row in records:
            attrs = (
                f' data-method="{_text(row["method"])}" data-status="{_text(row["status"])}"'
                f' data-kind="{kind}"'
            )
            rows.append(
                _row(
                    [
                        _text(row["method"]),
                        f"{_text(row['task'])} / {_text(row['family'])}",
                        _text(row["generation_seed"]),
                        f"{_text(row['sequence'])} / {_text(row['rep'])}",
                        _text(row.get("stage") if kind == "stop" else row["step"]),
                        _text(row["change_id"]),
                        _status(row["status"]),
                        _text(row["infra_cause"] or row["end_reason"]),
                    ],
                    attrs,
                )
            )
        parts.append(
            _table(
                headers,
                rows,
                "One initial stop per sample; later stops per trajectory."
                if kind == "stop"
                else "One row per planned change. Counts are diagnostics.",
            )
        )
        if kind == "stop":
            if not records:
                parts.append("<p>No initial non-passes or editing stops recorded.</p>")
            parts.append("<h3>All planned checkpoints</h3>")
    parts += [
        '</section><section class="panel"><h2>Files and interpretation</h2>',
        '<nav class="downloads" aria-label="Report files">',
    ]
    for name in (
        "report.md",
        "summary.csv",
        "comparisons.csv",
        "families.csv",
        "trajectories.csv",
        "checkpoints.csv",
        "failures.csv",
        "resources.csv",
        "source_descriptives.csv",
        "comparison.json",
        "manifest.json",
    ):
        parts.append(f'<a href="{name}" download>{name}</a>')
    parts.append("</nav><ul>")
    parts.extend(f"<li>{escape(note)}</li>" for note in result["notes"])
    parts += [
        "</ul><p>Verify this bundle with <code>python -m harness evaluation-verify "
        "--report DIRECTORY</code> before sharing. Checksums do not authenticate "
        "experimental claims.</p></section></main>",
        f"<script>{SCRIPT}</script></body></html>\n",
    ]
    return "\n".join(parts)
