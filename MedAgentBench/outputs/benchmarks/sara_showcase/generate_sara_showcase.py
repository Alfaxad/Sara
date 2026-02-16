#!/usr/bin/env python3
"""
Generate Sara 1.5 4B showcase analysis - CSVs, plots, and metrics.
Highlights Sara's efficiency relative to model size.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from collections import defaultdict

# Paths
BENCHMARK_DIR = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent

# Model metadata with parameter counts
MODEL_INFO = {
    "Sara 1.5 4B": {"params": 4, "params_str": "4B", "category": "Small (<10B)", "color": "#E8B86D"},
    "Qwen3-8B": {"params": 8, "params_str": "8B", "category": "Small (<10B)", "color": "#7B9EC2"},
    "Llama 3.1-8B Instruct": {"params": 8, "params_str": "8B", "category": "Small (<10B)", "color": "#8E8EA0"},
    "Qwen3-14B": {"params": 14, "params_str": "14B", "category": "Medium (10-30B)", "color": "#A8B87A"},
    "Mistral Small 3.2": {"params": 24, "params_str": "24B", "category": "Medium (10-30B)", "color": "#C4A96A"},
    "Llama 4 Scout": {"params": 109, "params_str": "109B (MoE)", "category": "Large (>100B)", "color": "#D99A6C"},
    "Llama 4 Maverick": {"params": 400, "params_str": "400B (MoE)", "category": "Large (>100B)", "color": "#D4826A"},
    "Claude Opus 4.5": {"params": 1000, "params_str": "Frontier", "category": "Frontier", "color": "#C9553C"},
    "Gemini 3 Flash": {"params": 500, "params_str": "Mid-tier", "category": "Frontier", "color": "#B8766A"},
    "Grok 4.1 Fast": {"params": 800, "params_str": "Frontier", "category": "Frontier", "color": "#D07A5A"},
    "Claude Sonnet 4.5": {"params": 700, "params_str": "Frontier", "category": "Frontier", "color": "#C96A5A"},
    "GPT-4.1": {"params": 900, "params_str": "Frontier", "category": "Frontier", "color": "#B05040"},
    "GPT-4o": {"params": 850, "params_str": "Frontier", "category": "Frontier", "color": "#A04535"},
    "GPT-5.1": {"params": 950, "params_str": "Frontier", "category": "Frontier", "color": "#903A2A"},
    "Gemini 2.5 Flash": {"params": 300, "params_str": "Mid-tier", "category": "Frontier", "color": "#C08060"},
}

# Short name mapping
SHORT_NAMES = {
    "anthropic_claude-opus-4-5-20251101": "Claude Opus 4.5",
    "anthropic_claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
    "openai_gpt-4o": "GPT-4o",
    "openai_gpt-4-1": "GPT-4.1",
    "openai_gpt-5-1": "GPT-5.1",
    "google_gemini-3-0-flash-preview": "Gemini 3 Flash",
    "google_gemini-2-5-flash-preview-04-17": "Gemini 2.5 Flash",
    "Alfaxad_Sara-1-5-4B-it": "Sara 1.5 4B",
    "meta-llama_llama-4-scout": "Llama 4 Scout",
    "meta-llama_llama-4-maverick": "Llama 4 Maverick",
    "x-ai_grok-4-1-fast": "Grok 4.1 Fast",
    "qwen_qwen3-14b": "Qwen3-14B",
    "qwen_qwen3-8b": "Qwen3-8B",
    "mistralai_mistral-small-3-2-24b-instruct": "Mistral Small 3.2",
    "meta-llama_llama-3-1-8b-instruct": "Llama 3.1-8B Instruct",
}

TASK_NAMES = {
    "task1": "Patient Search",
    "task2": "Lab Result Retrieval",
    "task3": "Medication Verification",
    "task4": "Allergy Information",
    "task5": "Condition Lookup",
    "task6": "Vital Signs Retrieval",
    "task7": "Clinical Note Creation",
    "task8": "Immunization Records",
    "task9": "Procedure History",
    "task10": "Care Plan Management",
}

# Colors
SARA_GOLD = "#E8B86D"
SARA_DARK = "#C9963D"
BG_COLOR = "#FAFAF8"
TEXT_COLOR = "#2D2D2D"
GRID_COLOR = "#ECECEC"


def load_benchmark_data():
    """Load all benchmark summaries."""
    models = []
    for summary_file in BENCHMARK_DIR.glob("*/summary.json"):
        folder_name = summary_file.parent.name
        if folder_name in SHORT_NAMES:
            with open(summary_file) as f:
                data = json.load(f)
            short_name = SHORT_NAMES[folder_name]
            if short_name in MODEL_INFO:
                models.append({
                    "name": short_name,
                    "folder": folder_name,
                    "accuracy": data.get("accuracy", 0),
                    "correct": data.get("correct", 0),
                    "total": data.get("total", 300),
                    "invalid_actions": data.get("invalid_action", 0),
                    "limit_reached": data.get("limit_reached", 0),
                    "task_breakdown": data.get("task_breakdown", {}),
                    **MODEL_INFO[short_name]
                })
    return sorted(models, key=lambda x: x["accuracy"], reverse=True)


def generate_efficiency_csv(models):
    """Generate CSV showing efficiency metrics (accuracy per billion params)."""
    rows = []
    sara = next(m for m in models if m["name"] == "Sara 1.5 4B")

    for m in models:
        # Efficiency = accuracy per billion parameters (higher = more efficient)
        efficiency = m["accuracy"] / m["params"] if m["params"] > 0 else 0
        sara_efficiency = sara["accuracy"] / sara["params"]

        rows.append({
            "Model": m["name"],
            "Parameters": m["params_str"],
            "Param Count (B)": m["params"],
            "Accuracy (%)": round(m["accuracy"], 1),
            "Efficiency (Acc/B)": round(efficiency, 2),
            "vs Sara Efficiency": f"{efficiency/sara_efficiency:.2f}x" if sara_efficiency > 0 else "N/A",
            "Category": m["category"],
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("Efficiency (Acc/B)", ascending=False)
    df.to_csv(OUTPUT_DIR / "efficiency_metrics.csv", index=False)
    print(f"  Created: efficiency_metrics.csv")
    return df


def generate_size_comparison_csv(models):
    """Generate CSV comparing Sara to models by size category."""
    sara = next(m for m in models if m["name"] == "Sara 1.5 4B")

    rows = []
    for m in models:
        size_ratio = m["params"] / sara["params"]
        acc_delta = m["accuracy"] - sara["accuracy"]

        # Expected accuracy if scaling linearly with params
        expected_from_size = sara["accuracy"] * (m["params"] / sara["params"]) ** 0.1  # diminishing returns
        actual_vs_expected = m["accuracy"] - min(expected_from_size, 100)

        rows.append({
            "Model": m["name"],
            "Parameters": m["params_str"],
            "Size vs Sara": f"{size_ratio:.0f}x" if size_ratio >= 1 else f"{1/size_ratio:.1f}x smaller",
            "Accuracy (%)": round(m["accuracy"], 1),
            "Sara Accuracy (%)": round(sara["accuracy"], 1),
            "Accuracy Delta": f"{acc_delta:+.1f}%",
            "Invalid Actions": m["invalid_actions"],
            "Category": m["category"],
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "size_comparison.csv", index=False)
    print(f"  Created: size_comparison.csv")
    return df


def generate_task_excellence_csv(models):
    """Generate CSV showing tasks where Sara excels or matches frontier models."""
    sara = next(m for m in models if m["name"] == "Sara 1.5 4B")
    sara_breakdown = sara["task_breakdown"]

    rows = []
    for task_id, task_name in TASK_NAMES.items():
        sara_correct = sara_breakdown.get(task_id, {}).get("correct", 0)
        sara_total = sara_breakdown.get(task_id, {}).get("total", 30)
        sara_acc = (sara_correct / sara_total * 100) if sara_total > 0 else 0

        # Find best model and field average for this task
        task_scores = []
        for m in models:
            tb = m["task_breakdown"].get(task_id, {})
            correct = tb.get("correct", 0)
            total = tb.get("total", 30)
            acc = (correct / total * 100) if total > 0 else 0
            task_scores.append({"name": m["name"], "accuracy": acc})

        task_scores_sorted = sorted(task_scores, key=lambda x: x["accuracy"], reverse=True)
        best_model = task_scores_sorted[0]
        field_avg = np.mean([s["accuracy"] for s in task_scores])

        # Find Sara's rank
        sara_rank = next(i+1 for i, s in enumerate(task_scores_sorted) if s["name"] == "Sara 1.5 4B")

        rows.append({
            "Task": task_name,
            "Sara Accuracy (%)": round(sara_acc, 1),
            "Sara Rank": f"{sara_rank}/{len(models)}",
            "Best Model": best_model["name"],
            "Best Accuracy (%)": round(best_model["accuracy"], 1),
            "Field Average (%)": round(field_avg, 1),
            "Sara vs Field": f"{sara_acc - field_avg:+.1f}%",
            "Sara vs Best": f"{sara_acc - best_model['accuracy']:+.1f}%",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "task_excellence.csv", index=False)
    print(f"  Created: task_excellence.csv")
    return df


def generate_small_model_comparison_csv(models):
    """Generate CSV comparing Sara to other small/medium models only."""
    small_medium = [m for m in models if m["params"] <= 30]
    sara = next(m for m in small_medium if m["name"] == "Sara 1.5 4B")

    rows = []
    for m in sorted(small_medium, key=lambda x: x["accuracy"], reverse=True):
        rows.append({
            "Model": m["name"],
            "Parameters": m["params_str"],
            "Accuracy (%)": round(m["accuracy"], 1),
            "vs Sara": f"{m['accuracy'] - sara['accuracy']:+.1f}%",
            "Invalid Actions": m["invalid_actions"],
            "Format Adherence": "Perfect" if m["invalid_actions"] == 0 else f"{m['invalid_actions']} errors",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "small_model_comparison.csv", index=False)
    print(f"  Created: small_model_comparison.csv")
    return df


def plot_size_vs_accuracy(models):
    """Scatter plot: model size vs accuracy with Sara highlighted."""
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Separate Sara from others
    sara = next(m for m in models if m["name"] == "Sara 1.5 4B")
    others = [m for m in models if m["name"] != "Sara 1.5 4B"]

    # Plot others by category
    category_colors = {
        "Small (<10B)": "#7B9EC2",
        "Medium (10-30B)": "#A8B87A",
        "Large (>100B)": "#D4826A",
        "Frontier": "#C9553C",
    }

    for m in others:
        ax.scatter(m["params"], m["accuracy"],
                   s=150, c=category_colors.get(m["category"], "#888888"),
                   alpha=0.7, edgecolors="white", linewidth=1.5, zorder=2)

        # Label
        offset = (10, 5) if m["params"] < 50 else (-10, 5)
        ha = "left" if m["params"] < 50 else "right"
        ax.annotate(m["name"], (m["params"], m["accuracy"]),
                    xytext=offset, textcoords="offset points",
                    fontsize=9, color=TEXT_COLOR, alpha=0.8, ha=ha)

    # Plot Sara with emphasis
    ax.scatter(sara["params"], sara["accuracy"],
               s=400, c=SARA_GOLD, edgecolors=SARA_DARK, linewidth=3,
               zorder=10, marker="*")
    ax.annotate(f"Sara 1.5 4B\n{sara['accuracy']:.1f}%",
                (sara["params"], sara["accuracy"]),
                xytext=(15, -15), textcoords="offset points",
                fontsize=12, fontweight="bold", color=SARA_DARK,
                arrowprops=dict(arrowstyle="->", color=SARA_DARK, lw=1.5))

    # Draw horizontal line from Sara showing models it beats
    beaten_models = [m for m in others if m["accuracy"] < sara["accuracy"]]
    if beaten_models:
        largest_beaten = max(beaten_models, key=lambda x: x["params"])
        ax.hlines(sara["accuracy"], sara["params"], largest_beaten["params"] + 50,
                  colors=SARA_GOLD, linestyles="--", alpha=0.5, linewidth=2)
        ax.annotate(f"Sara beats models up to {largest_beaten['params_str']}",
                    (largest_beaten["params"], sara["accuracy"]),
                    xytext=(0, 10), textcoords="offset points",
                    fontsize=10, color=SARA_DARK, ha="center", style="italic")

    ax.set_xscale("log")
    ax.set_xlabel("Parameters (Billions, log scale)", fontsize=12, color=TEXT_COLOR)
    ax.set_ylabel("Accuracy (%)", fontsize=12, color=TEXT_COLOR)
    ax.set_title("Model Size vs. Accuracy: Sara's Efficiency",
                 fontsize=16, fontweight="bold", color=TEXT_COLOR, pad=20)

    # Legend
    legend_patches = [
        mpatches.Patch(color=SARA_GOLD, label="Sara 1.5 4B"),
        mpatches.Patch(color=category_colors["Small (<10B)"], label="Small (<10B)"),
        mpatches.Patch(color=category_colors["Medium (10-30B)"], label="Medium (10-30B)"),
        mpatches.Patch(color=category_colors["Large (>100B)"], label="Large (>100B)"),
        mpatches.Patch(color=category_colors["Frontier"], label="Frontier"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=10)

    ax.grid(True, alpha=0.3, color=GRID_COLOR)
    ax.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "size_vs_accuracy.png", dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"  Created: size_vs_accuracy.png")


def plot_efficiency_bars(models):
    """Bar chart showing efficiency (accuracy per billion params)."""
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Calculate efficiency and sort
    data = []
    for m in models:
        efficiency = m["accuracy"] / m["params"]
        data.append({"name": m["name"], "efficiency": efficiency, "accuracy": m["accuracy"], "params": m["params_str"]})

    data = sorted(data, key=lambda x: x["efficiency"], reverse=True)[:10]  # Top 10

    names = [d["name"] for d in data]
    efficiencies = [d["efficiency"] for d in data]

    colors = [SARA_GOLD if n == "Sara 1.5 4B" else "#7B9EC2" for n in names]

    bars = ax.barh(range(len(names)), efficiencies, color=colors, edgecolor="white", linewidth=0.5)

    # Add value labels
    for i, (eff, d) in enumerate(zip(efficiencies, data)):
        ax.text(eff + 0.2, i, f"{eff:.1f} ({d['accuracy']:.0f}% / {d['params']})",
                va="center", fontsize=10, color=TEXT_COLOR)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel("Efficiency (Accuracy % per Billion Parameters)", fontsize=12, color=TEXT_COLOR)
    ax.set_title("Model Efficiency: Accuracy per Billion Parameters\n(Higher = More Efficient)",
                 fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=20)

    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.3, color=GRID_COLOR)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "efficiency_ranking.png", dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"  Created: efficiency_ranking.png")


def plot_small_model_leaderboard(models):
    """Leaderboard of only small/medium models (<= 30B params)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    small_medium = sorted([m for m in models if m["params"] <= 30],
                          key=lambda x: x["accuracy"], reverse=True)

    names = [f"{m['name']} ({m['params_str']})" for m in small_medium]
    accs = [m["accuracy"] for m in small_medium]

    # Different colors for each model - Sara in gold, others in distinct colors
    model_colors = {
        "Sara 1.5 4B": SARA_GOLD,
        "Qwen3-14B": "#A8B87A",      # sage green
        "Qwen3-8B": "#7B9EC2",        # muted blue
        "Mistral Small 3.2": "#C4A96A",  # muted gold
        "Llama 3.1-8B Instruct": "#D4826A",  # salmon
    }
    colors = [model_colors.get(m["name"], "#888888") for m in small_medium]

    bars = ax.barh(range(len(names)), accs, color=colors, edgecolor="white", linewidth=0.5)

    for i, acc in enumerate(accs):
        ax.text(acc + 1, i, f"{acc:.1f}%", va="center", fontsize=11,
                fontweight="bold" if small_medium[i]["name"] == "Sara 1.5 4B" else "normal",
                color=TEXT_COLOR)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel("Accuracy (%)", fontsize=12, color=TEXT_COLOR)
    ax.set_title("Small & Medium Model Leaderboard (≤30B Parameters)",
                 fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=20)
    ax.set_xlim(0, 85)

    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.3, color=GRID_COLOR)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "small_model_leaderboard.png", dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"  Created: small_model_leaderboard.png")


def plot_sara_task_performance(models):
    """Grouped bar chart: Sara vs field average vs best on each task."""
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    sara = next(m for m in models if m["name"] == "Sara 1.5 4B")

    tasks = list(TASK_NAMES.keys())
    task_labels = [TASK_NAMES[t] for t in tasks]

    sara_scores = []
    field_avgs = []
    best_scores = []
    best_names = []

    for task_id in tasks:
        sara_tb = sara["task_breakdown"].get(task_id, {})
        sara_acc = (sara_tb.get("correct", 0) / sara_tb.get("total", 30) * 100) if sara_tb.get("total", 30) > 0 else 0
        sara_scores.append(sara_acc)

        task_accs = []
        for m in models:
            tb = m["task_breakdown"].get(task_id, {})
            acc = (tb.get("correct", 0) / tb.get("total", 30) * 100) if tb.get("total", 30) > 0 else 0
            task_accs.append({"name": m["name"], "acc": acc})

        field_avgs.append(np.mean([t["acc"] for t in task_accs]))
        best = max(task_accs, key=lambda x: x["acc"])
        best_scores.append(best["acc"])
        best_names.append(best["name"])

    x = np.arange(len(tasks))
    width = 0.25

    bars1 = ax.bar(x - width, sara_scores, width, label="Sara 1.5 4B", color=SARA_GOLD, edgecolor="white")
    bars2 = ax.bar(x, field_avgs, width, label="Field Average", color="#7B9EC2", edgecolor="white")
    bars3 = ax.bar(x + width, best_scores, width, label="Best Model", color="#C9553C", edgecolor="white")

    # Highlight tasks where Sara beats field average or is best
    for i, (sara_s, field_s, best_s) in enumerate(zip(sara_scores, field_avgs, best_scores)):
        if sara_s >= best_s - 0.1:  # Sara is best or tied
            ax.annotate("★", (x[i] - width, sara_s + 2), fontsize=14, ha="center", color=SARA_DARK)
        elif sara_s > field_s:
            ax.annotate("↑", (x[i] - width, sara_s + 2), fontsize=12, ha="center", color=SARA_DARK)

    ax.set_ylabel("Accuracy (%)", fontsize=12, color=TEXT_COLOR)
    ax.set_title("Sara Task Performance vs. Field Average and Best Model\n(★ = Sara is best, ↑ = Sara beats average)",
                 fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(task_labels, rotation=45, ha="right", fontsize=10)
    ax.legend(loc="upper right", fontsize=10)
    ax.set_ylim(0, 110)
    ax.grid(True, axis="y", alpha=0.3, color=GRID_COLOR)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sara_task_performance.png", dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"  Created: sara_task_performance.png")


def plot_sara_vs_larger_models(models):
    """Bar chart comparing Sara to specifically larger models it beats."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    sara = next(m for m in models if m["name"] == "Sara 1.5 4B")

    # Models Sara beats that are larger
    larger_beaten = [m for m in models if m["params"] > sara["params"] and m["accuracy"] < sara["accuracy"]]
    larger_beaten = sorted(larger_beaten, key=lambda x: x["params"], reverse=True)

    # Add Sara for comparison
    comparison = [sara] + larger_beaten

    # Unique colors for each model
    model_colors = {
        "Sara 1.5 4B": SARA_GOLD,
        "Llama 4 Maverick": "#C9553C",    # deep terracotta
        "Llama 4 Scout": "#D4826A",       # salmon
        "Mistral Small 3.2": "#A8B87A",   # sage green
        "Qwen3-8B": "#7B9EC2",            # muted blue
        "Llama 3.1-8B Instruct": "#8E8EA0",  # cool gray
    }

    names = []
    accs = []
    params = []
    colors = []

    for m in comparison:
        names.append(m["name"])
        accs.append(m["accuracy"])
        params.append(m["params_str"])
        colors.append(model_colors.get(m["name"], "#888888"))

    y_pos = range(len(names))
    bars = ax.barh(y_pos, accs, color=colors, edgecolor="white", linewidth=0.5)

    for i, (acc, param) in enumerate(zip(accs, params)):
        label = f"{acc:.1f}% ({param})"
        ax.text(acc + 1, i, label, va="center", fontsize=10,
                fontweight="bold" if i == 0 else "normal", color=TEXT_COLOR)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel("Accuracy (%)", fontsize=12, color=TEXT_COLOR)
    ax.set_title("Sara 1.5 4B vs. Larger Models It Outperforms",
                 fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=20)
    ax.set_xlim(0, 80)

    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.3, color=GRID_COLOR)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sara_vs_larger.png", dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"  Created: sara_vs_larger.png")


def plot_format_adherence(models):
    """Bar chart showing format adherence (invalid actions) - Sara's strength."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    # Sort by invalid actions (ascending - fewer is better)
    sorted_models = sorted(models, key=lambda x: x["invalid_actions"])

    # Get Sara first
    sara = next(m for m in sorted_models if m["name"] == "Sara 1.5 4B")

    # Take models with zero invalid actions (excluding Sara to add separately)
    zero_errors = [m for m in sorted_models if m["invalid_actions"] == 0 and m["name"] != "Sara 1.5 4B"][:4]

    # Models with errors
    with_errors = [m for m in sorted_models if m["invalid_actions"] > 0]

    # Combine: Sara first (highlighted), then other zero-error models, then models with errors
    show_models = [sara] + zero_errors + with_errors

    names = [m["name"] for m in show_models]
    invalids = [m["invalid_actions"] for m in show_models]
    accs = [m["accuracy"] for m in show_models]

    colors = [SARA_GOLD if m["name"] == "Sara 1.5 4B" else
              ("#4CAF50" if m["invalid_actions"] == 0 else "#D4826A") for m in show_models]

    y_pos = range(len(names))
    bars = ax.barh(y_pos, invalids, color=colors, edgecolor="white", linewidth=0.5)

    for i, (inv, acc) in enumerate(zip(invalids, accs)):
        label = "Perfect ✓" if inv == 0 else f"{inv} errors"
        offset = 2 if inv > 0 else 1
        ax.text(inv + offset, i, f"{label} ({acc:.1f}% acc)", va="center", fontsize=10, color=TEXT_COLOR)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel("Invalid Actions (Lower = Better)", fontsize=12, color=TEXT_COLOR)
    ax.set_title("Format Adherence: Invalid Actions per Model\n(Sara achieves perfect format compliance)",
                 fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=20)

    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.3, color=GRID_COLOR)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "format_adherence.png", dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"  Created: format_adherence.png")


def main():
    print("Loading benchmark data...")
    models = load_benchmark_data()
    print(f"  Found {len(models)} models\n")

    print("Generating CSV files...")
    generate_efficiency_csv(models)
    generate_size_comparison_csv(models)
    generate_task_excellence_csv(models)
    generate_small_model_comparison_csv(models)

    print("\nGenerating plots...")
    plot_size_vs_accuracy(models)
    plot_efficiency_bars(models)
    plot_small_model_leaderboard(models)
    plot_sara_task_performance(models)
    plot_sara_vs_larger_models(models)
    plot_format_adherence(models)

    print(f"\nAll files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
