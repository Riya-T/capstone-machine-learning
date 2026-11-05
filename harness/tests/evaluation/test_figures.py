"""Scientific figures preserve uncertainty, unknown values, labels and replay bytes.

Usage:
    uv run pytest tests/evaluation/test_figures.py
"""

import json
import xml.etree.ElementTree as ET

import pytest

pytest.importorskip("matplotlib", reason="Install optional plots extra")

from matplotlib.figure import Figure
from PIL import Image

from harness.evaluation.analysis import compare
from harness.evaluation.figures import _rate_points, export_figures
from harness.evaluation.integrity import verify_report
from harness.evaluation.report import write_report

from .test_analysis import example


def test_unknown_rate_is_text_not_a_point_at_zero_and_intervals_can_exclude_estimate():
    figure = Figure()
    axis = figure.subplots()
    _rate_points(
        axis,
        ["known", "missing"],
        [dict(estimate=0.9, interval=[0.1, 0.2]), dict(estimate=None, interval=None)],
    )
    points = [line for line in axis.lines if line.get_marker() == "o"]
    assert len(points) == 1 and list(points[0].get_xdata()) == [0.9]
    assert any(text.get_text() == "unavailable" for text in axis.texts)


def test_figures_are_labeled_reproducible_and_keep_saved_plot_data(tmp_path):
    original = example()
    original["samples"][0]["trials"][0]["steps"] = []
    original["samples"][0]["writer_cost"]["tokens_in"] = None
    primary, out = tmp_path / "primary", tmp_path / "figures"
    write_report(compare([original, example("candidate")], bootstrap_samples=20), primary)
    paths = export_figures(primary, out)
    first = {name: (out / name).read_bytes() for name in paths}
    assert export_figures(primary, out) == paths
    assert first == {name: (out / name).read_bytes() for name in paths}
    data = json.loads((out / "figure_data.json").read_text())
    assert data["methods"]["original"]["metrics"]["change_completion"]["estimate"] is None
    assert data["methods"]["original"]["costs"]["tokens_in"]["missing_records"] == 1
    assert data["source_report_sha256"] and data["render_environment"]["matplotlib"]
    svg = (out / "outcomes.svg").read_text(encoding="utf8")
    assert "SYNTHETIC FIXTURE" in svg and "unavailable" in svg
    ET.fromstring(svg)
    with Image.open(out / "outcomes.png") as image:
        assert image.width > 900 and image.height > 500
    assert verify_report(out)["kind"] == "figures"


def test_single_method_has_no_invented_comparison(tmp_path):
    write_report(compare([example()], bootstrap_samples=20), tmp_path / "primary")
    export_figures(tmp_path / "primary", tmp_path / "figures")
    svg = (tmp_path / "figures/differences.svg").read_text(encoding="utf8")
    assert "No non-reference comparison available" in svg
