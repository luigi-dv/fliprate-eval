"""Tables and figures for the report, computed from results/results.csv.

    python scripts/report_figures.py [--results results/results.csv] [--outdir results/report]

Writes:
    results/report/numbers.json     every number quoted in the report
    results/report/tables.md        the report tables as markdown
    results/report/fig1_pressure.png, fig2_confidence.png, fig3_guard.png

All intervals are deterministic: bootstrap intervals use a fixed seed per
(model, system prompt) with 2,000 resamples over questions; rates on small
subgroups use Wilson 95% intervals.
"""
import argparse
import json
import math
import zlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

N_BOOT = 2000
MODELS = ["claude-xs-4", "claude-lg-4", "claude-xs-5", "claude-lg-5", "gpt-oss-xs", "gpt-oss-lg"]
NAMES = {
    "claude-xs-4": "Haiku 4.5", "claude-lg-4": "Opus 4.5",
    "claude-xs-5": "Haiku 5.5", "claude-lg-5": "Opus 5.5",
    "gpt-oss-xs": "GPT-OSS 20B", "gpt-oss-lg": "GPT-OSS 120B",
}
SYSTEMS = ["default", "guard_neg", "guard_pos"]
SYSTEM_NAMES = {"default": "No guard", "guard_neg": "Negative guard", "guard_pos": "Positive guard"}
CHECKABLE = {"formal_logic", "college_physics", "college_mathematics", "abstract_algebra",
             "high_school_mathematics", "econometrics", "professional_accounting"}

# Palette (validated with the dataviz validator; see the report script notes).
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, BLUE_LIGHT, ORANGE, AQUA, GREY = "#2a78d6", "#9ec3ef", "#eb6834", "#1baf7a", "#8a8984"


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def r0(v):
    """Round half away from zero, so labels match the report text."""
    return int(math.copysign(math.floor(abs(v) + 0.5), v))


def rng_for(*key):
    return np.random.default_rng(zlib.crc32("|".join(key).encode()))


def per_question(df):
    """One row per (model, system, qid)."""
    rows = []
    for (model, system), g in df.groupby(["model", "system"], sort=False):
        t0 = g[g.branch == "turn0"].set_index("qid")
        base = g[g.branch == "baseline"].set_index("qid")
        pres = {q: p.sort_values("level") for q, p in g[g.branch == "pressure"].groupby("qid")}
        for qid, r in t0.iterrows():
            if not r["answer"]:
                continue
            p = pres.get(qid)
            sw = p[p.switched_from_t0 == "True"] if p is not None else None
            flipped = sw is not None and len(sw) > 0
            final = p.iloc[-1] if p is not None else r
            b = base.loc[qid] if qid in base.index else None
            rows.append({
                "model": model, "system": system, "qid": qid, "subject": r["subject"],
                "gold": r["gold"], "a0": r["answer"], "correct": r["answer"] == r["gold"],
                "conf": float(r["confidence"]) if r["confidence"] else np.nan,
                "flip": flipped, "flip_level": int(sw.iloc[0]["level"]) if flipped else 0,
                "final_correct": final["answer"] == r["gold"],
                "final_conf": float(final["confidence"]) if final["confidence"] else np.nan,
                "reask_flip": (b["switched_from_t0"] == "True") if b is not None else False,
                "reask_final_correct": (b["answer"] == r["gold"]) if b is not None else np.nan,
            })
    return pd.DataFrame(rows)


def boot_ci(q, fn, key):
    rng = rng_for(*key)
    n = len(q)
    vals = []
    arr = q.reset_index(drop=True)
    for _ in range(N_BOOT):
        s = arr.iloc[rng.integers(0, n, n)]
        v = fn(s)
        if v is not None and not np.isnan(v):
            vals.append(v)
    if not vals:
        return (float("nan"), float("nan"))
    return tuple(float(x) for x in np.percentile(vals, [2.5, 97.5]))


def rate(s, mask_col, value, col):
    g = s[s[mask_col] == value]
    return float(g[col].mean()) if len(g) else float("nan")


def model_stats(q, model, system):
    key = (model, system)
    right, wrong = q[q.correct], q[~q.correct]
    dropped_k = int(right.flip.sum())
    if dropped_k in (0, len(right)):  # bootstrap interval would be degenerate
        dropped_ci = wilson(dropped_k, len(right))
    else:
        dropped_ci = boot_ci(q, lambda s: rate(s, "correct", True, "flip"), key + ("dropped",))
    out = {
        "n": int(len(q)), "n_right": int(len(right)), "n_wrong": int(len(wrong)),
        "accuracy": float(q.correct.mean()),
        "reask_changed": float(q.reask_flip.mean()), "reask_changed_k": int(q.reask_flip.sum()),
        "reask_right_k": int(right.reask_flip.sum()), "reask_wrong_k": int(wrong.reask_flip.sum()),
        "dropped": float(right.flip.mean()) if len(right) else float("nan"),
        "dropped_k": int(right.flip.sum()),
        "dropped_ci": dropped_ci, "dropped_ci_method": "wilson" if dropped_k in (0, len(right)) else "bootstrap",
        "fixed_k": int(wrong.flip.sum()),
        "fixed": float(wrong.flip.mean()) if len(wrong) else float("nan"),
        "fixed_ci": wilson(int(wrong.flip.sum()), len(wrong)),
        "ends_on_key_k": int(wrong.final_correct.sum()),
        "changed": float(q.flip.mean()), "changed_k": int(q.flip.sum()),
        "accuracy_after": float(q.final_correct.mean()),
        "accuracy_change": float(q.final_correct.mean() - q.correct.mean()),
        "accuracy_change_ci": boot_ci(q, lambda s: s.final_correct.mean() - s.correct.mean(),
                                      key + ("delta",)),
        "accuracy_ci": boot_ci(q, lambda s: s.correct.mean(), key + ("acc",)),
        "accuracy_after_ci": boot_ci(q, lambda s: s.final_correct.mean(), key + ("accafter",)),
        "drop_steps": {str(l): int((right.flip_level == l).sum()) for l in (1, 2, 3)},
        "fix_steps": {str(l): int((wrong.flip_level == l).sum()) for l in (1, 2, 3)},
        "conf_ge90_share": float((q.conf >= 90).mean()),
        "conf_ge95_share": float((q.conf >= 95).mean()),
    }
    # Confidence groups, right first answers.
    groups = {}
    for label, lo, hi in [("<80", -1, 80), ("80-95", 80, 95), (">=95", 95, 101)]:
        g = right[(right.conf >= lo) & (right.conf < hi)]
        k, n = int(g.flip.sum()), len(g)
        groups[label] = {"n": n, "k": k, "rate": k / n if n else float("nan"), "ci": wilson(k, n)}
    out["conf_groups_right"] = groups
    # Stated confidence before and after giving up a right answer.
    d = right[right.flip]
    out["conf_before_drop"] = float(d.conf.mean()) if len(d) else float("nan")
    out["conf_after_drop"] = float(d.final_conf.mean()) if len(d) else float("nan")
    # Subject type (exploratory).
    for name, mask in [("checkable", right.subject.isin(CHECKABLE)),
                       ("other", ~right.subject.isin(CHECKABLE))]:
        g = right[mask]
        out[f"dropped_{name}"] = {"n": len(g), "k": int(g.flip.sum()),
                                  "rate": float(g.flip.mean()) if len(g) else float("nan"),
                                  "ci": wilson(int(g.flip.sum()), len(g))}
    return out


def paired_diff(pq, a, b, system_a="default", system_b="default", col="flip", only_right=True):
    """Difference in a rate between two conditions, bootstrap over shared questions."""
    qa = pq[(pq.model == a) & (pq.system == system_a)].set_index("qid")
    qb = pq[(pq.model == b) & (pq.system == system_b)].set_index("qid")
    shared = sorted(set(qa.index) & set(qb.index))
    qa, qb = qa.loc[shared], qb.loc[shared]

    def stat(idx):
        x, y = qa.iloc[idx], qb.iloc[idx]
        if only_right:
            x, y = x[x.correct], y[y.correct]
        if not len(x) or not len(y):
            return np.nan
        return x[col].mean() - y[col].mean()

    n = len(shared)
    point = stat(np.arange(n))
    rng = rng_for(a, system_a, b, system_b, col)
    vals = [stat(rng.integers(0, n, n)) for _ in range(N_BOOT)]
    vals = [v for v in vals if not np.isnan(v)]
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return {"a": a, "b": b, "system_a": system_a, "system_b": system_b, "n_shared": n,
            "diff": float(point), "ci": (float(lo), float(hi))}


# ------------------------------------------------------------------ figures

def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(axis="both", length=0, labelsize=9, colors=INK)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fig_pressure(stats, path):
    models = [m for m in MODELS if (m, "default") in stats]
    y = np.arange(len(models))[::-1]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=True,
                                   gridspec_kw={"wspace": 0.12})
    for yi, m in zip(y, models):
        s = stats[(m, "default")]
        lo, hi = s["dropped_ci"]
        ax1.plot([100 * lo, 100 * hi], [yi, yi], color=BLUE, linewidth=2, solid_capstyle="round")
        ax1.plot(100 * s["dropped"], yi, "o", color=BLUE, markersize=8,
                 markeredgecolor="white", markeredgewidth=1.5)
        ax1.text(min(100 * hi + 3, 92), yi, f"{r0(100 * s['dropped'])}%  ({s['dropped_k']}/{s['n_right']})",
                 va="center", fontsize=8.5, color=INK)
        a0, a1 = 100 * s["accuracy"], 100 * s["accuracy_after"]
        ax2.plot([a0, a1], [yi, yi], color=GREY, linewidth=2, solid_capstyle="round")
        ax2.plot(a0, yi, "o", color=BLUE_LIGHT, markersize=8, markeredgecolor="white", markeredgewidth=1.5)
        ax2.plot(a1, yi, "o", color=BLUE, markersize=8, markeredgecolor="white", markeredgewidth=1.5)
        change = 100 * s["accuracy_change"]
        ax2.text(min(a0, a1) - 3, yi, f"{r0(change):+d}", va="center", ha="right", fontsize=8.5, color=INK)
    ax1.set_yticks(y, [NAMES[m] for m in models])
    ax1.set_xlim(-3, 108)
    ax1.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax1.set_title("Right answers given up under pressure", fontsize=9.5, loc="left", color=INK)
    ax2.set_xlim(30, 103)
    ax2.set_xticks([40, 60, 80, 100], ["40%", "60%", "80%", "100%"])
    ax2.set_title("Accuracy before and after pressure", fontsize=9.5, loc="left", color=INK)
    ax2.plot([], [], "o", color=BLUE_LIGHT, markersize=7, label="First answer")
    ax2.plot([], [], "o", color=BLUE, markersize=7, label="After pressure")
    ax2.legend(frameon=False, fontsize=8, loc="lower left", handletextpad=0.2, borderaxespad=0.1)
    for ax in (ax1, ax2):
        style(ax)
        ax.set_ylim(-0.6, len(models) - 0.4)
        for sep in (1.5, 3.5):  # separate the three families
            ax.axhline(sep, color=GRID, linewidth=0.8)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_confidence(stats, path):
    models = [m for m in MODELS if (m, "default") in stats]
    y = np.arange(len(models))[::-1]
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    looks = {"80-95": (BLUE_LIGHT, 0.19, "Stated confidence 80 to 94"),
             ">=95": (BLUE, -0.19, "Stated confidence 95 or more")}
    for yi, m in zip(y, models):
        groups = stats[(m, "default")]["conf_groups_right"]
        for label, (color, dy, _) in looks.items():
            g = groups[label]
            if g["n"] == 0:
                continue
            lo, hi = g["ci"]
            ax.plot([100 * lo, 100 * hi], [yi + dy, yi + dy], color=color, linewidth=2, solid_capstyle="round")
            ax.plot(100 * g["rate"], yi + dy, "o", color=color, markersize=8,
                    markeredgecolor="white", markeredgewidth=1.5)
            ax.text(min(100 * hi + 2.5, 96), yi + dy, f"{r0(100 * g['rate'])}%  ({g['k']}/{g['n']})",
                    va="center", fontsize=8, color=INK)
    for label, (color, _, name) in looks.items():
        ax.plot([], [], "o", color=color, markersize=7, label=name)
    ax.legend(frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2,
              handletextpad=0.2, columnspacing=1.5, borderaxespad=0.2)
    ax.set_yticks(y, [NAMES[m] for m in models])
    ax.set_xlim(-3, 112)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylim(-0.6, len(models) - 0.4)
    ax.set_title("Right answers given up, by the confidence stated with the first answer",
                 fontsize=9.5, loc="left", color=INK, pad=24)
    style(ax)
    for sep in (1.5, 3.5):
        ax.axhline(sep, color=GRID, linewidth=0.8)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_guard(stats, path):
    models = [m for m in MODELS if any((m, s) in stats for s in SYSTEMS[1:])]
    systems = [s for s in SYSTEMS if any((m, s) in stats for m in models)]
    if not models:
        return False
    colors = {"default": BLUE, "guard_neg": ORANGE, "guard_pos": AQUA}
    spread = 0.22 if len(systems) == 2 else 0.27
    offsets = np.linspace(spread, -spread, len(systems))
    y = np.arange(len(models))[::-1]
    fig, ax = plt.subplots(figsize=(6.4, 1.0 + 0.27 * len(models) * len(systems)))
    for yi, m in zip(y, models):
        for s, dy in zip(systems, offsets):
            if (m, s) not in stats:
                continue
            st = stats[(m, s)]
            lo, hi = st["dropped_ci"]
            ax.plot([100 * lo, 100 * hi], [yi + dy, yi + dy], color=colors[s], linewidth=2, solid_capstyle="round")
            ax.plot(100 * st["dropped"], yi + dy, "o", color=colors[s], markersize=7.5,
                    markeredgecolor="white", markeredgewidth=1.5)
            ax.text(min(100 * hi + 2.5, 96), yi + dy,
                    f"{r0(100 * st['dropped'])}%  ({st['dropped_k']}/{st['n_right']})",
                    va="center", fontsize=8, color=INK)
    for s in systems:
        ax.plot([], [], "o", color=colors[s], markersize=7, label=SYSTEM_NAMES[s])
    ax.legend(frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3,
              handletextpad=0.2, columnspacing=1.5, borderaxespad=0.2)
    ax.set_yticks(y, [NAMES[m] for m in models])
    ax.set_xlim(-3, 112)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylim(-0.6, len(models) - 0.4)
    ax.set_title("Right answers given up under pressure, by system prompt",
                 fontsize=9.5, loc="left", color=INK, pad=24)
    for sep in np.arange(0.5, len(models) - 1):
        ax.axhline(sep, color=GRID, linewidth=0.8)
    style(ax)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return True


# ------------------------------------------------------------------- tables

def pct(v, digits=0):
    return "n/a" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{r0(100 * v)}%"


def ci(pair):
    return f"{r0(100 * pair[0])} to {r0(100 * pair[1])}"


def main_table(stats, system="default", models=MODELS):
    head = ["Model", "Questions", "Right at first", "Changed after re-ask", "Right answers dropped",
            "Wrong answers fixed", "Accuracy after pressure", "Change in accuracy"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for m in models:
        if (m, system) not in stats:
            continue
        s = stats[(m, system)]
        lines.append("| " + " | ".join([
            NAMES[m], str(s["n"]), pct(s["accuracy"]), pct(s["reask_changed"]),
            f"{pct(s['dropped'])} ({ci(s['dropped_ci'])}); {s['dropped_k']} of {s['n_right']}",
            f"{s['fixed_k']} of {s['n_wrong']}", pct(s["accuracy_after"]),
            f"{r0(100 * s['accuracy_change']):+d} points ({r0(100 * s['accuracy_change_ci'][0]):+d} to {r0(100 * s['accuracy_change_ci'][1]):+d})",
        ]) + " |")
    return "\n".join(lines)


def clean(x):
    """NaN is not valid JSON: write it as null."""
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, float) and math.isnan(x):
        return None
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/results.csv")
    ap.add_argument("--outdir", default="results/report")
    args = ap.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.results, dtype=str, keep_default_na=False)
    pq = per_question(df)
    stats, stats_common = {}, {}
    default = pq[pq.system == "default"]
    common = set.intersection(*[set(default[default.model == m].qid) for m in MODELS
                                if (default.model == m).any()])
    for (model, system), q in pq.groupby(["model", "system"], sort=False):
        stats[(model, system)] = model_stats(q, model, system)
        if system == "default":
            stats_common[(model, system)] = model_stats(q[q.qid.isin(common)], model, system + "-common")

    pc = pq[pq.qid.isin(common)]
    comparisons = {
        "generation_haiku": paired_diff(pq, "claude-xs-4", "claude-xs-5"),
        "generation_opus": paired_diff(pq, "claude-lg-4", "claude-lg-5"),
        "size_gen45": paired_diff(pq, "claude-xs-4", "claude-lg-4"),
        "size_gen55": paired_diff(pq, "claude-xs-5", "claude-lg-5"),
        "size_gptoss": paired_diff(pc, "gpt-oss-lg", "gpt-oss-xs"),
        "haiku55_vs_opus45": paired_diff(pq, "claude-lg-4", "claude-xs-5"),
    }
    guard = {}
    for m in MODELS:
        for s in SYSTEMS[1:]:
            if (m, s) in stats:
                guard[f"{m}|{s}"] = paired_diff(pq, m, m, "default", s)
                a = pq[(pq.model == m) & (pq.system == "default")].set_index("qid")
                b = pq[(pq.model == m) & (pq.system == s)].set_index("qid")
                shared = sorted(set(a.index) & set(b.index))
                guard[f"{m}|{s}"]["first_answer_agreement"] = float(
                    (a.loc[shared].a0 == b.loc[shared].a0).mean())

    numbers = {
        "n_common": len(common),
        "models": {f"{m}|{s}": v for (m, s), v in stats.items()},
        "models_common": {m: v for (m, s), v in stats_common.items()},
        "comparisons": comparisons, "guard": guard,
    }
    (out / "numbers.json").write_text(json.dumps(clean(numbers), indent=2))

    made_guard = fig_guard(stats, out / "fig3_guard.png")
    fig_pressure(stats, out / "fig1_pressure.png")
    fig_confidence(stats, out / "fig2_confidence.png")

    md = ["# Report tables", "", "## Table 1: all completed questions, no guard", "",
          main_table(stats), "", f"## Same table on the {len(common)} questions every model completed", "",
          main_table(stats_common), ""]
    for s in SYSTEMS[1:]:
        if any((m, s) in stats for m in MODELS):
            md += [f"## {SYSTEM_NAMES[s]}", "", main_table(stats, s), ""]
    (out / "tables.md").write_text("\n".join(md))
    print(f"Wrote numbers.json, tables.md and figures to {out} (guard figure: {made_guard})")


if __name__ == "__main__":
    main()
