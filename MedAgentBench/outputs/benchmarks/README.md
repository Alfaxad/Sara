# MedAgentBench Benchmarking Results

This directory contains benchmark results, analysis, and visualizations for 15 LLMs evaluated on [MedAgentBench](https://ai.nejm.org/doi/full/10.1056/AIdbp2500144), a benchmark for medical LLM agents operating in a virtual EHR environment.

## Quick Summary

| Rank | Model | Parameters | Accuracy |
|:----:|-------|------------|:--------:|
| 1 | Claude Opus 4.5 | Frontier | **95.0%** |
| 2 | Gemini 3 Flash Preview | Mid-tier | **90.0%** |
| 3 | Grok 4.1 Fast | Frontier | **87.7%** |
| 4 | Claude Sonnet 4.5 | Frontier | **86.0%** |
| 5 | GPT-4.1 | Frontier | **77.3%** |
| 6 | GPT-4o | Frontier | **77.0%** |
| 7 | GPT-5.1 | Frontier | **76.0%** |
| 8 | Qwen3-14B | 14B | **74.0%** |
| 9 | Gemini 2.5 Flash | Mid-tier | **72.8%** |
| 10 | Sara 1.5 4B | 4B | **66.7%** |
| 11 | Mistral Small 3.2 | 24B | **51.7%** |
| 12 | Llama 4 Scout | 109B (MoE) | **41.3%** |
| 13 | Qwen3-8B | 8B | **40.0%** |
| 14 | Llama 4 Maverick | 400B (MoE) | **37.3%** |
| 15 | Llama 3.1-8B Instruct | 8B | **14.0%** |

**Key Finding:** Sara 1.5 4B (4 billion parameters) outperforms Llama 4 Scout (109B), Llama 4 Maverick (400B), Qwen3-8B (8B), and Mistral Small 3.2 (24B), demonstrating that targeted fine-tuning on 284 examples can beat models up to 100x larger.

## Directory Structure

```
outputs/benchmarks/
├── README.md                      # This file
├── BENCHMARKING_REPORT.md         # Full technical report (~4,200 words)
│
├── plots/                         # Visualizations (300 DPI PNG)
│   ├── leaderboard.png            # Overall model rankings
│   ├── task_heatmap.png           # Task-by-task accuracy matrix
│   ├── sara_vs_field.png          # Sara performance vs field average
│   ├── task_difficulty.png        # Score distribution by task (dark theme)
│   └── task_grouped_bars.png      # Per-task comparison of selected models
│
├── *.csv                          # Analysis tables
│   ├── leaderboard.csv            # Overall rankings with metrics
│   ├── task_accuracy_matrix.csv   # Full 10x10 accuracy matrix
│   ├── task_rankings.csv          # Per-task model rankings (1st-10th)
│   ├── model_rankings_per_task.csv# Each model's rank per task
│   ├── sara_comparison.csv        # Sara vs field average per task
│   ├── task_difficulty.csv        # Tasks ranked by difficulty
│   └── task_analysis.csv          # Combined analysis table
│
└── <model_name>/                  # Per-model results (15 directories)
    ├── runs.jsonl                 # Raw task-by-task results
    └── summary.json               # Aggregated metrics and breakdown
```

## Benchmark Details

### Evaluation Protocol

- **Tasks:** 300 clinical EHR tasks across 10 task types
- **Attempts:** Single attempt per task (pass@1)
- **Max Rounds:** 8 interaction rounds per task
- **Environment:** FHIR R4 server with 100 patient profiles (700K+ records)

### Task Types

| Task | Description | Type | Avg Accuracy |
|------|-------------|------|:------------:|
| Task 1 | Patient Search | Query | 78.3% |
| Task 2 | Lab Result Retrieval | Query | 87.7% |
| Task 3 | Medication Verification | Action | 73.0% |
| Task 4 | Allergy Information | Query | 83.3% |
| Task 5 | Condition Lookup | Action | 84.7% |
| Task 6 | Vital Signs Retrieval | Query | 57.7% |
| Task 7 | Clinical Note Creation | Query | 38.7% |
| Task 8 | Immunization Records | Action | 92.0% |
| Task 9 | Procedure History | Action | 58.3% |
| Task 10 | Care Plan Management | Action | 66.0% |

**Hardest Task:** Clinical Note Creation (Task 7) at 38.7% average - even Claude Opus 4.5 only achieved 57%.

**Easiest Task:** Immunization Records (Task 8) at 92.0% average.

### Models Evaluated

| Model | Provider | API Endpoint |
|-------|----------|--------------|
| Claude Opus 4.5 | Anthropic | OSV Engineering |
| Claude Sonnet 4.5 | Anthropic | OSV Engineering |
| GPT-4o | OpenAI | OSV Engineering |
| GPT-4.1 | OpenAI | OSV Engineering |
| GPT-5.1 | OpenAI | OSV Engineering |
| Gemini 3 Flash Preview | Google | OpenRouter |
| Gemini 2.5 Flash | Google | OpenRouter |
| Grok 4.1 Fast | xAI | OpenRouter |
| Qwen3-14B | Alibaba | OpenRouter |
| Qwen3-8B | Alibaba | OpenRouter |
| Mistral Small 3.2 24B | Mistral | OpenRouter |
| Llama 3.1-8B Instruct | Meta | OpenRouter |
| Sara 1.5 4B | Alfaxad | Modal (self-hosted) |
| Llama 4 Scout | Meta | OpenRouter |
| Llama 4 Maverick | Meta | OpenRouter |

## Sara 1.5 4B Highlights

Sara 1.5 4B is a fine-tuned variant of MedGemma-1.5-4B-it, trained on 284 correct interaction traces.

> **Detailed Analysis:** See the [Sara Showcase](sara_showcase/SARA_SHOWCASE.md) for in-depth efficiency metrics, size comparisons, and visualizations demonstrating Sara's remarkable performance relative to its parameter count.

### State-of-the-Art Performance (4 tasks)

| Task | Sara Score | 2nd Place | Notes |
|------|:----------:|-----------|-------|
| Task 9: Procedure History | **96.7%** | Claude Opus 4.5 (93.3%) | Beats all frontier models |
| Task 1: Patient Search | **100%** | Tied with 4 models | Perfect score |
| Task 4: Allergy Information | **100%** | Tied with 2 models | Perfect score |
| Task 8: Immunization Records | **100%** | Tied with 6 models | Perfect score |

### Size vs Performance

| Model | Parameters | Accuracy | vs Sara |
|-------|:----------:|:--------:|:-------:|
| Sara 1.5 4B | 4B | 66.7% | baseline |
| Mistral Small 3.2 | 24B (6x larger) | 51.7% | -15.0% |
| Llama 4 Scout | 109B (27x larger) | 41.3% | -25.4% |
| Qwen3-8B | 8B (2x larger) | 40.0% | -26.7% |
| Llama 4 Maverick | 400B (100x larger) | 37.3% | -29.4% |
| Llama 3.1-8B Instruct | 8B (2x larger) | 14.0% | -52.7% |

### Format Adherence

| Model | Invalid Actions |
|-------|:---------------:|
| Sara 1.5 4B | **0** |
| Mistral Small 3.2 | **0** |
| Grok 4.1 Fast | **0** |
| Llama 3.1-8B Instruct | 14 |
| Qwen3-14B | 23 |
| Llama 4 Scout | 34 |
| Qwen3-8B | 93 |
| Llama 4 Maverick | 116 |

## Reproducing Results

### Prerequisites

```bash
# Clone MedAgentBench and install dependencies
cd MedAgentBench
pip install -r requirements.txt

# Start FHIR server (Docker required)
docker pull jyxsu6/medagentbench:latest
docker run -p 8080:8080 jyxsu6/medagentbench:latest
```

### Running Benchmarks

```bash
# Benchmark a model via OSV Engineering
python benchmark_models.py \
    --model "anthropic/claude-opus-4-5-20251101" \
    --base-url "https://developer.osv.engineering/inference/v1" \
    --api-key "YOUR_API_KEY"

# Benchmark via OpenRouter
python benchmark_models.py \
    --model "google/gemini-2.5-flash" \
    --base-url "https://openrouter.ai/api/v1" \
    --api-key "YOUR_OPENROUTER_KEY" \
    --extra-header "HTTP-Referer=https://your-site.com" \
    --extra-header "X-Title=YourProject"

# Benchmark a self-hosted model (e.g., on Modal)
python benchmark_models.py \
    --model "Alfaxad/Sara-1.5-4B-it" \
    --base-url "https://your-modal-endpoint.modal.run/v1" \
    --api-key "unused"
```

### Generating Analysis

```bash
# Generate CSV analysis files
python generate_csvs.py

# Generate visualizations
python visualize_benchmarks.py

# Run terminal analysis
python analyze_benchmarks.py
```

## File Formats

### runs.jsonl

Each line is a JSON object with task results:

```json
{
  "index": 0,
  "task_id": "task1_1",
  "status": "completed",
  "correct": true,
  "result": ["S6534835"],
  "num_turns": 2,
  "time": "2026-02-05 11:23:45"
}
```

**Status values:** `completed`, `agent_invalid_action`, `limit_reached`, `context_limit`, `error`

### summary.json

Aggregated metrics for a model run:

```json
{
  "model": "anthropic/claude-opus-4-5-20251101",
  "total": 300,
  "completed": 300,
  "correct": 285,
  "invalid_action": 0,
  "limit_reached": 0,
  "context_limit": 0,
  "error": 0,
  "task_breakdown": {
    "task1": {"total": 30, "correct": 30},
    "task2": {"total": 30, "correct": 30},
    ...
  },
  "elapsed_seconds": 1670.49,
  "accuracy": 95.0
}
```

## Visualizations

### Leaderboard
![Leaderboard](plots/leaderboard.png)

### Task-by-Task Heatmap
![Heatmap](plots/task_heatmap.png)

### Sara vs Field Average
![Sara Comparison](plots/sara_vs_field.png)

### Task Difficulty Distribution
![Task Difficulty](plots/task_difficulty.png)

### Per-Task Model Comparison
![Grouped Bars](plots/task_grouped_bars.png)

## Scripts

| Script | Description |
|--------|-------------|
| `benchmark_models.py` | Run benchmarks on any OpenAI-compatible API |
| `generate_csvs.py` | Generate all CSV analysis files |
| `visualize_benchmarks.py` | Generate all PNG visualizations |
| `analyze_benchmarks.py` | Print terminal analysis and task_analysis.csv |

## Citation

If you use these benchmark results, please cite the original MedAgentBench paper:

```bibtex
@article{jiang2025medagentbench,
  title={MedAgentBench: A Virtual EHR Environment to Benchmark Medical LLM Agents},
  author={Jiang, Yixing and Black, Kameron C and Geng, Gloria and Park, Danny
          and Zou, James and Ng, Andrew Y and Chen, Jonathan H},
  journal={NEJM AI},
  pages={AIdbp2500144},
  year={2025},
  publisher={Massachusetts Medical Society}
}
```

## License

Benchmark results and analysis scripts are provided for research purposes. See the main MedAgentBench repository for licensing terms.
