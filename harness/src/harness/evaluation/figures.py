"""Export reproducible PNG/SVG figures from verified saved comparison records.

Usage:
    export_figures(report_directory, output_directory)
    # Install the optional plots extra; no model or container is contacted.
"""

from __future__ import annotations

import io
import platform
import textwrap

from .artifacts import encoded, publish_bundle, purpose_label, read_comparison
from .records import EvaluationError


def figure_data(result, source_hash):
    # Figures consume the saved estimates and intervals, not selected successful trials.
    return dict(
        purpose=result["purpose"],
        reference=result["reference"],
        source_report_sha256=source_hash,
        bootstrap=result["bootstrap"],
        methods={
            name: {key: row[key] for key in ("metrics", "costs", "counts")}
            for name, row in result["methods"].items()
        },
        comparisons=result["comparisons"],
    )


def _rate_points(ax, names, metrics, *, difference=False):
    from matplotlib.ticker import FuncFormatter, PercentFormatter

    for position, values in enumerate(metrics):
        estimate = values.get("difference") if difference else values.get("estimate")
        interval = values.get("interval")
        if estimate is None:
            ax.text(
                0.03 if not difference else -0.95,
                position,
                "unavailable",
                va="center",
                color="#6b7280",
            )
            continue
        if interval is not None:
            # Draw interval endpoints independently; a percentile interval need not
            # contain its point estimate, so asymmetric error lengths can be negative.
            ax.hlines(position, interval[0], interval[1], color="#2d5b94", linewidth=2)
            ax.plot(
                interval, [position, position], "|", color="#2d5b94", markersize=9, clip_on=False
            )
        ax.plot(estimate, position, "o", color="#163c6a", markersize=6, clip_on=False)
    ax.set_yticks(range(len(names)), [textwrap.fill(name, 25) for name in names])
    ax.set_ylim(len(names) - 0.5, -0.5)
    ax.set_xlim((-1, 1) if difference else (0, 1))
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f"{100 * x:+.0f} pp") if difference else PercentFormatter(1)
    )
    ax.grid(axis="x", alpha=0.2)
    if difference:
        ax.axvline(0, color="#777", linestyle=":", linewidth=1)
    for edge in ("top", "right"):
        ax.spines[edge].set_visible(False)


def export_figures(directory, output):
    result, source_hash = read_comparison(directory)
    try:
        import matplotlib
        import numpy
        import PIL
        from matplotlib.figure import Figure
    except ImportError as error:
        raise EvaluationError(
            "Install plotting support with: uv sync --locked --extra plots"
        ) from error
    data = figure_data(result, source_hash)
    data["render_environment"] = dict(
        matplotlib=matplotlib.__version__,
        numpy=numpy.__version__,
        pillow=PIL.__version__,
        python=platform.python_version(),
        platform=platform.system() + "/" + platform.machine(),
    )
    files = {}
    names = list(result["methods"])
    caption = (
        f"{result['bootstrap']['confidence']:.0%} exploratory task-family intervals; "
        "no interval bar when unavailable. Repetitions are not independent evidence."
    )

    def save(name, figure):
        for extension in ("png", "svg"):
            stream = io.BytesIO()
            metadata = {"Software": "capstone-evaluation"} if extension == "png" else {"Date": None}
            figure.savefig(
                stream, format=extension, dpi=180, bbox_inches="tight", metadata=metadata
            )
            files[name + "." + extension] = stream.getvalue()
        figure.clear()

    # A fixed SVG hash salt and absent timestamps make same-version replay stable.
    # No interactive plotting backend or network asset is needed.
    with matplotlib.rc_context(
        {
            "svg.hashsalt": "capstone-evaluation",
            "svg.fonttype": "none",
            "font.family": "DejaVu Sans",
            "font.size": 10,
        }
    ):
        outcomes = Figure(figsize=(13, max(7, len(names) * 0.9 + 2)), layout="constrained")
        axes = outcomes.subplots(2, 2).flat
        for ax, key, title in zip(
            axes,
            (
                "initial_correctness",
                "change_completion",
                "whole_sequence_success",
                "regression_rate_reached",
            ),
            (
                "Initial correctness",
                "Changes completed before failure",
                "Whole-sequence success",
                "Regressions among evaluated steps (lower is better)",
            ),
            strict=True,
        ):
            _rate_points(ax, names, [result["methods"][n]["metrics"][key] for n in names])
            ax.set_title(title, fontsize=11)
        outcomes.suptitle(purpose_label(result), fontsize=14)
        outcomes.supxlabel(caption, fontsize=9)
        save("outcomes", outcomes)

        pairs = result["comparisons"]
        differences = Figure(figsize=(10, max(3.5, len(pairs) * 0.65 + 2)), layout="constrained")
        ax = differences.subplots()
        if pairs:
            _rate_points(
                ax,
                [p["method"] for p in pairs],
                [p["metrics"]["change_completion"] for p in pairs],
                difference=True,
            )
            ax.set_xlabel("Absolute completion difference from reference (percentage points)")
        else:
            ax.text(0.5, 0.5, "No non-reference comparison available", ha="center", va="center")
            ax.set_axis_off()
        differences.suptitle(
            purpose_label(result) + "\nReference: " + result["reference"], fontsize=13
        )
        differences.supxlabel(caption, fontsize=8)
        save("differences", differences)

        resources = Figure(figsize=(14, max(4, len(names) * 0.55 + 2)), layout="constrained")
        for ax, key, title in zip(
            resources.subplots(1, 3),
            ("tokens_in", "tokens_out", "wall_s"),
            ("Recorded input tokens", "Recorded output tokens", "Recorded wall seconds"),
            strict=True,
        ):
            measurements = [result["methods"][n]["costs"][key] for n in names]
            totals = [v["known_total"] for v in measurements]
            ax.barh(range(len(names)), totals, color="#527cab")
            ax.set_yticks(range(len(names)), [textwrap.fill(n, 22) for n in names])
            ax.invert_yaxis()
            ax.set_title(title, fontsize=11)
            ax.set_xlim(0, max(1, max(totals)) * 1.6)
            for position, row in enumerate(measurements):
                label = f"{row['known_total']:g}"
                if row["missing_records"]:
                    label += f" known; {row['missing_records']} missing"
                ax.text(row["known_total"], position, " " + label, va="center", fontsize=8)
            ax.grid(axis="x", alpha=0.2)
        resources.suptitle(purpose_label(result), fontsize=14)
        resources.supxlabel(
            "Known recorded totals, not normalized efficiency. Tokens may include estimates; "
            "wall time includes latency. Reached work differs between methods.",
            fontsize=8,
        )
        save("resources", resources)
    data["notes"] = [
        caption,
        "Synthetic/development labels remain on every figure.",
        "Resource figures display known totals and missing fields, not dollar charges.",
    ]
    files["figure_data.json"] = encoded(data)
    files["report.md"] = (
        f"# {purpose_label(result)}\n\nPNG and SVG figures use the saved estimates "
        "and intervals. figure_data.json records the plotted values, "
        "source report hash and renderer "
        "version. Unknown outcomes are not plotted as zero.\n\n" + caption + "\n"
    ).encode("utf8")
    return publish_bundle("figures", files, output, source_hash=source_hash)
