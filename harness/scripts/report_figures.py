"""Figures for the final report, from the store and the saved result files.

Writes a PNG and an SVG of each figure to harness/results/figures/:

- methods: each writer against the base writer on the 16 eval tasks, the
  difference in changes done before the first failure and in how often
  its samples pass the initial checks, with paired task-bootstrap 95%
  intervals (as `scripts/eval_compare.py`).
- variance: how the variance of one trial's score within a task splits
  into the program, the program on that sequence and the trial (the
  editor's randomness), for the base writer's train, dev and eval
  programs (as `scripts/diagnostics.py`).
- label_noise: how often each Radon writer's implicit reward ranks the
  held-out Radon pairs of the eval tasks like MI, by the kind and amount
  of noise in its training labels (`runs/rtx5070_pc/dpo/
  implicit_reward_noise.jsonl`, `implicit_reward_scorenoise.jsonl`).
- heldout: the same for the Radon pairs and the base writer's held-out
  eval-task editing pairs side by side (`implicit_reward_dpoall.jsonl`),
  with what a writer that learned the editing signal as well as
  radon_rel18_all learned MI would get on labels this noisy
  (`scripts/noise_ceiling.py`, at the eval tasks' reliability).

Each implicit-reward figure also shows two rankers without training: the
base model's own log-probability and "the chosen program is the shorter".

Usage (from harness/, inside WSL; matplotlib is the `plots` extra):
    .venv/bin/python scripts/report_figures.py
    .venv/bin/python scripts/report_figures.py --only methods \
        --writer "DPO, every editing pair=configs/rtx5070_eval_dpo_all.yaml"
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from diagnostics import reliability, scored_programs, variance_components, variance_sums  # noqa: E402
from eval_compare import rate  # noqa: E402
from eval_summary import percentile_interval, task_results  # noqa: E402
from implicit_reward import accuracy_interval, file_pairs  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402
from noise_ceiling import ceiling, load_programs  # noqa: E402

from harness.config import load_config  # noqa: E402

DPO = Path("runs/rtx5070_pc/dpo")
WRITERS = {
    "Maintainability prompt": "configs/rtx5070_eval_maintain.yaml",
    "Static ranking (Radon)": "configs/rtx5070_eval_radon.yaml",
    "Correctness-only fine-tuning": "configs/rtx5070_eval_sft.yaml",
    "DPO on editing outcomes (dpo3)": "configs/rtx5070_eval_dpo3.yaml",
}
# The reference palette's light steps (first three categorical slots, which
# pass the colour-blindness checks for every pair) and its neutral inks.
INK, INK_2, INK_3 = "#0b0b0b", "#52514e", "#8b8a86"
GRID, SURFACE, NEUTRAL = "#e3e2de", "#fcfcfb", "#c9c8c3"
BLUE, ORANGE = "#2a78d6", "#eb6834"
REFERENCES = (("base", "Base model, no training"), ("shorter", "Shorter program wins"))


def style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.size": 9.5, "text.color": INK, "axes.labelcolor": INK_2,
        "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "x",
        "grid.color": GRID, "grid.linewidth": 0.8, "xtick.color": INK_2,
        "ytick.color": INK, "ytick.left": False, "xtick.major.size": 0,
        "svg.fonttype": "none",
    })  # fmt: skip


def title(fig, text) -> None:
    fig.suptitle(text, x=0.01, ha="left", fontsize=11, fontweight="bold")


def save(fig, out: Path, name: str) -> None:
    for ext in ("png", "svg"):
        fig.savefig(out / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out / name}.png and .svg")


def dot(ax, y, est, lo, hi, color, marker="o", text=None, label=None):
    """A point estimate with its 95% interval as a 2px line, and its value
    to the right of the interval."""
    ax.plot([lo, hi], [y, y], color=color, linewidth=2, solid_capstyle="round", zorder=2)
    ax.plot([est], [y], marker=marker, markersize=7.5, color=color, linestyle="none",
            markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3, label=label)  # fmt: skip
    if text:
        ax.annotate(text, (hi, y), xytext=(6, 0), textcoords="offset points", va="center",
                    color=INK_2, fontsize=8.5)  # fmt: skip


def chance_line(ax) -> None:
    ax.axvline(0.5, color=INK_3, linewidth=1, zorder=1)
    ax.annotate("chance", (0.5, 1), xycoords=("data", "axes fraction"), xytext=(0, 3),
                textcoords="offset points", ha="center", va="bottom", color=INK_2,
                fontsize=8)  # fmt: skip


def share_axis(ax) -> None:
    ax.set_xlim(0.2, 1.0)
    ax.set_xticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))


# --- methods ----------------------------------------------------------------


def paired(base_cfg, other_cfg, n, seed):
    """Difference (other minus base) in the main measure and the initial
    pass rate over the tasks both have trials on, with paired intervals."""
    base = {r["task_id"]: r for r in task_results(base_cfg)[0] if r["trials"]}
    other = {r["task_id"]: r for r in task_results(other_cfg)[0] if r["trials"]}
    common = sorted(base.keys() & other.keys())
    diffs = [(other[t]["mean"] - base[t]["mean"], rate(other[t]) - rate(base[t])) for t in common]
    (lo_m, hi_m), (lo_p, hi_p) = percentile_interval(diffs, n, seed)
    k = len(common)
    return {
        "tasks": k,
        "base": sum(base[t]["mean"] for t in common) / k,
        "other": sum(other[t]["mean"] for t in common) / k,
        "mean": (sum(d[0] for d in diffs) / k, lo_m, hi_m),
        "pass": (sum(d[1] for d in diffs) / k, lo_p, hi_p),
    }


def methods_figure(writers, out, n, seed):
    base_cfg = load_config("configs/rtx5070_eval.yaml")
    rows = [(label, paired(base_cfg, load_config(path), n, seed)) for label, path in writers]
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(10, 0.6 * len(rows) + 1.4), sharey=True, gridspec_kw={"wspace": 0.3}
    )
    ys = list(range(len(rows)))[::-1]
    for y, (_, r) in zip(ys, rows, strict=True):
        dot(left, y, *r["mean"], BLUE, text=f"{r['other']:.2f} vs {r['base']:.2f}")
        est, lo, hi = (100 * v for v in r["pass"])
        dot(right, y, est, lo, hi, BLUE, text=f"{est:+.0f}")
    for ax in (left, right):
        ax.axvline(0, color=INK_3, linewidth=1, zorder=1)
        ax.set_ylim(-0.6, len(rows) - 0.4)
    lo, hi = left.get_xlim()
    left.set_xlim(lo, hi + 0.35 * (hi - lo))
    lo, hi = right.get_xlim()
    right.set_xlim(lo, hi + 0.15 * (hi - lo))
    left.set_yticks(ys, [label for label, _ in rows])
    left.set_xlabel("Changes done before the first failure,\ndifference from the base writer")
    right.set_xlabel("Samples passing the initial tests,\ndifference from the base writer (points)")
    k = rows[0][1]["tasks"]
    title(fig, f"No method changes how far the editor gets ({k} eval tasks, 95% intervals)")
    save(fig, out, "methods")


# --- variance ---------------------------------------------------------------


def components(path):
    scores = scored_programs(load_config(path))[0]
    v = variance_components([variance_sums(p) for p in scores.values()])
    total = v["program"] + v["program x sequence"] + v["trial"]
    shares = [v[k] / total for k in ("program", "program x sequence", "trial")]
    return shares, reliability(v, v["s"], v["r"]), len(scores)


def variance_figure(out):
    rows = [("Train", "configs/rtx5070_train.yaml"), ("Dev", "configs/rtx5070_pc.yaml"),
            ("Eval", "configs/rtx5070_eval.yaml")]  # fmt: skip
    data = [(name, *components(path)) for name, path in rows]
    fig, ax = plt.subplots(figsize=(8, 2.2))
    names = ("Program", "Program on that sequence", "Trial (the editor's randomness)")
    colors = (BLUE, ORANGE, NEUTRAL)
    ys = list(range(len(data)))[::-1]
    for y, (_, shares, rel, _) in zip(ys, data, strict=True):
        left = 0.0
        for i, share in enumerate(shares):
            ax.barh(y, share, left=left, height=0.55, color=colors[i], edgecolor=SURFACE,
                    linewidth=2, label=names[i] if y == ys[0] else None)  # fmt: skip
            left += share
        ax.annotate(f"program {shares[0]:.0%}; a program's mean has reliability {rel:.2f}",
                    (1, y), xytext=(8, 0), textcoords="offset points", va="center",
                    color=INK_2, fontsize=8.5)  # fmt: skip
    ax.set_yticks(ys, [f"{name} ({tasks} tasks)" for name, _, _, tasks in data])
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlabel("Share of the variance of one trial's score within a task")
    ax.grid(False)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.3), ncol=3, frameon=False)
    title(fig, "The editor's randomness swamps the program")
    save(fig, out, "variance")
    return {name: rel for name, _, rel, _ in data}


# --- implicit reward --------------------------------------------------------


def rows_of(path, set_name):
    return [row for row in file_pairs(path) if row["set"] == set_name]


def ranked(rows, name, n, seed):
    """Share of pairs a ranker orders like their labels, with an interval."""
    if name == "base":
        return accuracy_interval(rows, lambda r: r["base_chosen"] > r["base_rejected"], n, seed)
    if name == "shorter":
        return accuracy_interval(rows, lambda r: r["chosen_tokens"] < r["rejected_tokens"], n, seed)

    def right(r):
        return r[f"{name}_chosen"] - r["base_chosen"] > r[f"{name}_rejected"] - r["base_rejected"]

    return accuracy_interval(rows, right, n, seed)


def label_noise_figure(out, n, seed):
    noise = rows_of(DPO / "implicit_reward_noise.jsonl", "radon_evaltasks.jsonl")
    score = rows_of(DPO / "implicit_reward_scorenoise.jsonl", "radon_evaltasks.jsonl")
    groups = [
        ("No noise", INK, "D", [("radon", "True labels, 160 pairs", noise)]),
        ("Random swaps", ORANGE, "s", [
            ("radon_f15", "15% of 160 pairs swapped", noise),
            ("radon_f30", "30% swapped (as often as ours disagree)", noise),
            ("radon_f50", "50% swapped", noise),
        ]),
        ("Noise per program", BLUE, "o", [
            ("radon_rel80", "Reliability 0.80, 160 pairs", score),
            ("radon_rel47", "Reliability 0.47, 160 pairs", score),
            ("radon_rel18", "Reliability 0.18 (ours), 160 pairs", score),
            ("radon_rel18s2", "Reliability 0.18, other seed, 160 pairs", score),
            ("radon_rel18_all", "Reliability 0.18, all 627 pairs", score),
        ]),
        ("No training", INK_3, "o", [(name, label, noise) for name, label in REFERENCES]),
    ]  # fmt: skip
    count = sum(len(items) for *_, items in groups) + len(groups) - 1
    fig, ax = plt.subplots(figsize=(8, 0.36 * count + 1.2))
    y, ticks = count - 1, []
    for group, color, marker, items in groups:
        for i, (name, label, rows) in enumerate(items):
            est, lo, hi = ranked(rows, name, n, seed)
            dot(ax, y, est, lo, hi, color, marker, f"{est:.0%}", group if i == 0 else None)
            ticks.append((y, label))
            y -= 1
        y -= 1  # a gap between groups
    chance_line(ax)
    ax.set_yticks([t for t, _ in ticks], [label for _, label in ticks])
    ax.set_ylim(-0.6, count - 0.4)
    share_axis(ax)
    ax.set_xlabel("Held-out Radon pairs of the 16 eval tasks ranked like MI (95% intervals)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False)
    title(fig, "Noise like ours hides the preference in 160 pairs, not in all of them")
    save(fig, out, "label_noise")


def heldout_figure(out, n, seed, eval_reliability):
    path = DPO / "implicit_reward_dpoall.jsonl"
    panels = [
        (rows_of(path, "radon_evaltasks.jsonl"), "Radon pairs ({}), labelled by MI"),
        (rows_of(path, "rtx5070_eval_aggregate.yaml"),
         "Editing pairs ({}), labelled by the editor"),
    ]  # fmt: skip
    writers = [
        ("radon", "Radon writer (160 true pairs)", INK, "D"),
        ("radon_rel18_all", "Radon at reliability 0.18 (627 pairs)", BLUE, "o"),
        ("dpo3", "DPO on editing outcomes (dpo3, 160 pairs)", ORANGE, "s"),
        ("dpo_all", "DPO on every editing pair (dpo_all, 634)", ORANGE, "s"),
    ] + [(name, label, INK_3, "o") for name, label in REFERENCES]
    programs = load_programs(DPO / "radon_evaltasks.jsonl", path, "radon_rel18_all")
    reliability = round(eval_reliability, 2)
    mean, low, high = ceiling(programs, reliability, 400, 1)  # noise_ceiling.py's defaults
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True, gridspec_kw={"wspace": 0.12})
    ys = [5.5, 4.5, 3.5, 2.5, 1, 0]
    for ax, (rows, heading) in zip(axes, panels, strict=True):
        for y, (name, _, color, marker) in zip(ys, writers, strict=True):
            est, lo, hi = ranked(rows, name, n, seed)
            dot(ax, y, est, lo, hi, color, marker, f"{est:.0%}")
        chance_line(ax)
        ax.set_title(heading.format(len(rows)), loc="left", fontsize=9.5, color=INK, pad=16)
        share_axis(ax)
        ax.set_ylim(-0.6, 6.1)
    axes[1].axvspan(low, high, color=BLUE, alpha=0.12, linewidth=0, zorder=0)
    axes[1].annotate(
        f"what a writer that learned\nthe editing signal as well\nas the 0.18 writer learned MI\n"
        f"would get: {mean:.0%} ({low:.0%} to {high:.0%};\nreliability {reliability})",
        (high, 0.5), xycoords=("data", "axes fraction"), xytext=(6, 0),
        textcoords="offset points", va="center", color=INK_2, fontsize=8,
    )  # fmt: skip
    axes[0].set_yticks(ys, [label for _, label, _, _ in writers])
    fig.supxlabel("Held-out pairs of the 16 eval tasks ranked like their labels (95% intervals)",
                  fontsize=9.5, color=INK_2, y=-0.03)  # fmt: skip
    title(fig, "With matched noise and pair count, DPO learns MI's preference, not the editor's")
    fig.subplots_adjust(top=0.8)
    save(fig, out, "heldout")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--writer", action="append", default=[], help="label=config")
    parser.add_argument("--only", action="append", default=[],
                        choices=("methods", "variance", "label_noise", "heldout"))  # fmt: skip
    parser.add_argument("--out", type=Path, default=Path("results/figures"))
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()
    writers = list(WRITERS.items()) + [tuple(w.split("=", 1)) for w in args.writer]
    wanted = set(args.only) or {"methods", "variance", "label_noise", "heldout"}
    args.out.mkdir(parents=True, exist_ok=True)
    style()
    if "methods" in wanted:
        methods_figure(writers, args.out, args.bootstrap, args.seed)
    if wanted & {"variance", "heldout"}:
        reliabilities = variance_figure(args.out)
    if "label_noise" in wanted:
        label_noise_figure(args.out, args.bootstrap, args.seed)
    if "heldout" in wanted:
        heldout_figure(args.out, args.bootstrap, args.seed, reliabilities["Eval"])


if __name__ == "__main__":
    main()
