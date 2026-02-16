#!/usr/bin/env python3
"""
Generate individual task plots showing top 5 performers for each task.
Creates 10 plots, one per task type.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Paths
BENCHMARK_DIR = Path(__file__).parent.parent
OUTPUT_DIR = Path(__file__).parent / "task_plots"
OUTPUT_DIR.mkdir(exist_ok=True)

# Model metadata with parameter counts
MODEL_INFO = {
    "Sara 1.5 4B": {"params": 4, "params_str": "4B", "category": "Small (<10B)"},
    "Qwen3-8B": {"params": 8, "params_str": "8B", "category": "Small (<10B)"},
    "Llama 3.1-8B Instruct": {"params": 8, "params_str": "8B", "category": "Small (<10B)"},
    "Qwen3-14B": {"params": 14, "params_str": "14B", "category": "Medium (10-30B)"},
    "Mistral Small 3.2": {"params": 24, "params_str": "24B", "category": "Medium (10-30B)"},
    "Llama 4 Scout": {"params": 109, "params_str": "109B (MoE)", "category": "Large (>100B)"},
    "Llama 4 Maverick": {"params": 400, "params_str": "400B (MoE)", "category": "Large (>100B)"},
    "Claude Opus 4.5": {"params": 1000, "params_str": "Frontier", "category": "Frontier"},
    "Gemini 3 Flash": {"params": 500, "params_str": "Mid-tier", "category": "Frontier"},
    "Grok 4.1 Fast": {"params": 800, "params_str": "Frontier", "category": "Frontier"},
    "Claude Sonnet 4.5": {"params": 700, "params_str": "Frontier", "category": "Frontier"},
    "GPT-4.1": {"params": 900, "params_str": "Frontier", "category": "Frontier"},
    "GPT-4o": {"params": 850, "params_str": "Frontier", "category": "Frontier"},
    "GPT-5.1": {"params": 950, "params_str": "Frontier", "category": "Frontier"},
    "Gemini 2.5 Flash": {"params": 300, "params_str": "Mid-tier", "category": "Frontier"},
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

TASK_INFO = {
    "task1": {"name": "Patient Search", "type": "Query", "description": "Search patient by name/DOB, return MRN"},
    "task2": {"name": "Lab Result Retrieval", "type": "Query", "description": "Calculate patient age from birthdate"},
    "task3": {"name": "Medication Verification", "type": "Action", "description": "Record blood pressure measurement"},
    "task4": {"name": "Allergy Information", "type": "Query", "description": "Retrieve recent magnesium level"},
    "task5": {"name": "Condition Lookup", "type": "Action", "description": "Check Mg level, order replacement if low"},
    "task6": {"name": "Vital Signs Retrieval", "type": "Query", "description": "Calculate average CBG over 24 hours"},
    "task7": {"name": "Clinical Note Creation", "type": "Query", "description": "Retrieve most recent CBG value"},
    "task8": {"name": "Immunization Records", "type": "Action", "description": "Create orthopedic surgery referral"},
    "task9": {"name": "Procedure History", "type": "Action", "description": "Check K+ level, order replacement + recheck"},
    "task10": {"name": "Care Plan Management", "type": "Action", "description": "Check HbA1C, order if stale (>1 year)"},
}

# Colors
SARA_GOLD = "#E8B86D"
SARA_DARK = "#C9963D"
BG_COLOR = "#FAFAF8"
TEXT_COLOR = "#2D2D2D"
GRID_COLOR = "#ECECEC"

# Category colors
CATEGORY_COLORS = {
    "Small (<10B)": "#7B9EC2",
    "Medium (10-30B)": "#A8B87A",
    "Large (>100B)": "#D99A6C",
    "Frontier": "#C9553C",
}


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
                    "task_breakdown": data.get("task_breakdown", {}),
                    **MODEL_INFO[short_name]
                })
    return models


def get_task_scores(models, task_id):
    """Get all model scores for a specific task."""
    scores = []
    for m in models:
        tb = m["task_breakdown"].get(task_id, {})
        correct = tb.get("correct", 0)
        total = tb.get("total", 30)
        acc = (correct / total * 100) if total > 0 else 0
        scores.append({
            "name": m["name"],
            "accuracy": acc,
            "correct": correct,
            "total": total,
            "params_str": m["params_str"],
            "category": m["category"],
        })
    return sorted(scores, key=lambda x: x["accuracy"], reverse=True)


def plot_task_top5(task_id, task_info, models):
    """Create a bar plot for top 5 models on a specific task."""
    scores = get_task_scores(models, task_id)
    top5 = scores[:5]

    # Check if Sara is in top 5, if not, note her rank
    sara_in_top5 = any(s["name"] == "Sara 1.5 4B" for s in top5)
    sara_score = next((s for s in scores if s["name"] == "Sara 1.5 4B"), None)
    sara_rank = next((i+1 for i, s in enumerate(scores) if s["name"] == "Sara 1.5 4B"), None)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    names = [f"{s['name']}\n({s['params_str']})" for s in top5]
    accs = [s["accuracy"] for s in top5]

    # Color bars: Sara in gold, others by category
    colors = []
    for s in top5:
        if s["name"] == "Sara 1.5 4B":
            colors.append(SARA_GOLD)
        else:
            colors.append(CATEGORY_COLORS.get(s["category"], "#888888"))

    bars = ax.bar(range(len(names)), accs, color=colors, edgecolor="white", linewidth=1.5, width=0.7)

    # Add value labels on top of bars
    for i, (bar, acc, s) in enumerate(zip(bars, accs, top5)):
        label = f"{acc:.1f}%"
        y_pos = bar.get_height() + 1
        fontweight = "bold" if s["name"] == "Sara 1.5 4B" else "normal"
        ax.text(bar.get_x() + bar.get_width()/2, y_pos, label,
                ha="center", va="bottom", fontsize=12, fontweight=fontweight, color=TEXT_COLOR)

        # Add rank badge
        ax.text(bar.get_x() + bar.get_width()/2, 3, f"#{i+1}",
                ha="center", va="bottom", fontsize=10, fontweight="bold",
                color="white", bbox=dict(boxstyle="circle,pad=0.3", facecolor=colors[i], edgecolor="white"))

    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=10, color=TEXT_COLOR)
    ax.set_ylabel("Accuracy (%)", fontsize=12, color=TEXT_COLOR)
    ax.set_ylim(0, 115)

    # Title with task info
    task_type_color = "#4CAF50" if task_info["type"] == "Query" else "#2196F3"
    task_num = task_id.replace("task", "")
    title = f"Task {task_num}: {task_info['name']}"
    subtitle = f"{task_info['description']}"

    ax.set_title(title, fontsize=16, fontweight="bold", color=TEXT_COLOR, pad=20, loc="left")
    ax.text(0.0, 1.02, subtitle, transform=ax.transAxes, fontsize=10, color="#666666", style="italic")

    # Add task type badge
    ax.text(0.98, 1.02, task_info["type"], transform=ax.transAxes, fontsize=10,
            ha="right", va="bottom", fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=task_type_color, edgecolor="none"))

    # If Sara not in top 5, add annotation about her rank
    if not sara_in_top5 and sara_score:
        note = f"Sara 1.5 4B: #{sara_rank} ({sara_score['accuracy']:.1f}%)"
        ax.text(0.98, 0.02, note, transform=ax.transAxes, fontsize=9,
                ha="right", va="bottom", color=SARA_DARK, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor=SARA_GOLD, alpha=0.3, edgecolor=SARA_DARK))

    ax.grid(True, axis="y", alpha=0.3, color=GRID_COLOR, zorder=0)
    ax.set_axisbelow(True)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    task_num = task_id.replace("task", "")
    filename = f"task{task_num}_{task_info['name'].lower().replace(' ', '_')}.png"
    plt.savefig(OUTPUT_DIR / filename, dpi=300, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close()

    return filename, sara_in_top5, sara_rank, sara_score["accuracy"] if sara_score else 0


def main():
    print("Loading benchmark data...")
    models = load_benchmark_data()
    print(f"  Found {len(models)} models\n")

    print("Generating task-by-task plots (Top 5 performers each)...")
    print("-" * 60)

    results = []
    for task_id, task_info in TASK_INFO.items():
        filename, sara_in_top5, sara_rank, sara_acc = plot_task_top5(task_id, task_info, models)
        status = "★ Sara in Top 5" if sara_in_top5 else f"Sara #{sara_rank} ({sara_acc:.1f}%)"
        print(f"  {task_id}: {task_info['name']:25s} → {filename:45s} {status}")
        results.append({
            "task": task_id,
            "name": task_info["name"],
            "sara_in_top5": sara_in_top5,
            "sara_rank": sara_rank,
            "sara_accuracy": sara_acc,
        })

    print("-" * 60)
    sara_top5_count = sum(1 for r in results if r["sara_in_top5"])
    print(f"\nSara in Top 5: {sara_top5_count}/10 tasks")
    print(f"Plots saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
