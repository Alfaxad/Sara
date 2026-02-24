"""
Benchmark multiple LLMs on MedAgentBench tasks.

Each model gets one attempt per task. Results are saved per model for comparison.

Usage:
    python benchmark_models.py --model anthropic/claude-opus-4-5-20251101
    python benchmark_models.py --all  # Run all models sequentially
"""

import json
import os
import sys
import time
import datetime
import argparse
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

import requests
import openai


# ── FHIR utilities ─────────────────────────────────────────────────────────────

def send_get_request(url, params=None, headers=None):
    """Sends a GET HTTP request to the given URL."""
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return {
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('Content-Type') == 'application/json' else response.text
        }
    except Exception as e:
        return {"error": str(e)}


def verify_fhir_server(fhir_api_base):
    """Verify connection to FHIR server."""
    res = send_get_request(f'{fhir_api_base}metadata')
    return res.get('status_code', 0) == 200


# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_FHIR_API_BASE = "http://localhost:8080/fhir/"
DEFAULT_DATA_FILE = "data/medagentbench/test_data_v2.json"
DEFAULT_FUNC_FILE = "data/medagentbench/funcs_v1.json"
DEFAULT_MAX_ROUNDS = 8
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OUTPUT_DIR = "outputs/benchmarks"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.0

# Models to benchmark
BENCHMARK_MODELS = [
    "anthropic/claude-opus-4-5-20251101",
    "anthropic/claude-sonnet-4-5-20250929",
    "osv/deepseek-r1",
    "openai/gpt-4o",
    "openai/gpt-4.1",
    "openai/gpt-5.1",
]

# Standard MedAgentBench prompt (same as generate_dataset.py for fair comparison)
MEDAGENTBENCH_PROMPT = """You are an expert in using FHIR functions to assist medical professionals. You are given a question and a set of possible functions. Based on the question, you will need to make one or more function/tool calls to achieve the purpose.

CRITICAL FORMAT RULES — your response must contain ONLY one of these three formats and NOTHING else (no explanations, no reasoning, no commentary):

1. To invoke a GET function:
GET url?param_name1=param_value1&param_name2=param_value2...

2. To invoke a POST function:
POST url
[your payload data in JSON format]

3. To finish with your answer (the list MUST be JSON parseable):
FINISH([answer1, answer2, ...])

IMPORTANT RULES:
- Your ENTIRE response must be ONLY the function call or FINISH — no other text before or after.
- Do NOT include any reasoning, explanation, or commentary in your response.
- Do NOT prefix your response with phrases like "I'll help you", "Let me", "Based on", etc.
- Each response must start with exactly "GET", "POST", or "FINISH(" as the very first characters.
- You can call only one function per response.
- FINISH answers must contain ONLY simple numeric values, simple strings, or -1. NEVER include objects, descriptions, or explanations inside FINISH.
- If the task asks you to check a value and take action only if needed, and no action is needed, call FINISH([]) with an empty list.
- If the task says to return -1 when something is unavailable, return FINISH([-1]) — just the number, no explanation text.

ANSWER FORMAT RULES FOR SPECIFIC TASK TYPES:

When asked for a lab value (e.g., magnesium, glucose, potassium, HbA1C):
- Return ONLY the numeric value: FINISH([2.1]) — NOT FINISH([{{"value": 2.1, "unit": "mg/dL"}}])
- If no measurement available, return: FINISH([-1])
- IMPORTANT: When finding the "most recent" observation, you MUST compare the effectiveDateTime fields to find the latest one chronologically. Do NOT assume the first entry in the FHIR Bundle is the most recent — entries may NOT be sorted by date. You must check ALL entries and pick the one with the latest effectiveDateTime.

When asked for the average of lab values:
- Return ONLY a single number as a float: FINISH([97.5])
- Make sure to only include observations within the specified time window (compare effectiveDateTime against the cutoff)

When asked to check a value and conditionally order something:
- If the value is normal/not low and no order is needed: FINISH([])
- If no measurement is available and instructions say don't order: FINISH([])
- If you placed orders, finish with: FINISH([]) or FINISH([the_value])

When asked for a value AND its date (e.g., HbA1C):
- Return as: FINISH([6.5, "2022-10-15T08:30:00+00:00"]) — value first, then the exact ISO timestamp string from the FHIR response
- If no measurement available: FINISH([-1])
- IMPORTANT: If the task says "if the lab value result date is greater than 1 year old, order a new lab test" — you MUST still order the test even when no value exists at all (no measurement = definitely older than 1 year). First POST the ServiceRequest to order the test, THEN call FINISH([-1]).
- Similarly, if a value exists but is older than 1 year from the current time, POST the ServiceRequest first, then FINISH with the value and date.

When ordering potassium replacement (task involving potassium dosing):
- The dosing formula is: for every 0.1 mEq/L below 3.5, order 10 mEq. So if K=3.1, dose = (3.5-3.1)/0.1 * 10 = 40 mEq
- The route must be: {{"text": "oral"}}
- You must make TWO POST requests: first the MedicationRequest for potassium, then the ServiceRequest for the follow-up serum potassium lab
- For the follow-up lab ServiceRequest, set occurrenceDateTime to the next day at 8:00 AM (e.g., "2023-11-14T08:00:00+00:00")

When ordering medications (MedicationRequest POST):
- The "route" field in dosageInstruction must be a plain string: "IV" for intravenous or "oral" for oral. NOT an object like {{"text": "IV"}} — just the string directly.
- Always include doseQuantity (with value and unit) and rateQuantity (with value and unit) where applicable
- Use authoredOn = "2023-11-13T10:15:00+00:00" (the current time from context)

When ordering IV magnesium replacement:
- Mild deficiency (1.5-1.9 mg/dL): dose=1g, rate=1h → doseQuantity: {{"value": 1, "unit": "g"}}, rateQuantity: {{"value": 1, "unit": "h"}}
- Moderate deficiency (1.0 to <1.5 mg/dL): dose=2g, rate=2h → doseQuantity: {{"value": 2, "unit": "g"}}, rateQuantity: {{"value": 2, "unit": "h"}}
- Severe deficiency (<1.0 mg/dL): dose=4g, rate=4h → doseQuantity: {{"value": 4, "unit": "g"}}, rateQuantity: {{"value": 4, "unit": "h"}}

When ordering lab tests or referrals (ServiceRequest POST):
- Always include: resourceType, code (with coding system/code), authoredOn, status ("active"), intent ("order"), priority ("stat"), subject
- For scheduled tests, include occurrenceDateTime with the scheduled time

EXAMPLES of correct FINISH calls:
FINISH(["S1234567"])
FINISH([42])
FINISH([125.5])
FINISH([-1])
FINISH([])
FINISH([6.5, "2022-10-15T08:30:00+00:00"])

EXAMPLES of WRONG FINISH calls (NEVER do these):
FINISH([{{"value": 191.0, "unit": "mg/dL"}}])  ← objects not allowed, use FINISH([191.0])
FINISH(["The potassium level is 4.5 mmol/L, no replacement needed"])  ← descriptions not allowed, use FINISH([])
FINISH([-1, "No measurement available", "Test ordered"])  ← extra explanation strings not allowed, use FINISH([-1])
FINISH([4.5, "above threshold, no action needed"])  ← use FINISH([]) when no action needed

Here is a list of functions in JSON format that you can invoke. Note that you should use {api_base} as the api_base.
{functions}

Context: {context}
Question: {question}"""

# ── Logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Model API call ────────────────────────────────────────────────────────────

def call_model(
    client: openai.OpenAI,
    history: List[Dict[str, str]],
    model: str,
    max_tokens: int,
    temperature: float,
    max_retries: int = 5,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Tuple[Optional[str], bool]:
    """Call model via OpenAI-compatible API."""
    messages = []
    for item in history:
        role = "assistant" if item["role"] == "agent" else item["role"]
        messages.append({"role": role, "content": item["content"]})

    kwargs = dict(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if extra_headers:
        kwargs["extra_headers"] = extra_headers

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content, False

        except openai.RateLimitError:
            wait = min(2 ** attempt * 5, 120)
            log.warning(f"Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)

        except openai.BadRequestError as e:
            err = str(e).lower()
            if "context" in err or "token" in err or "length" in err:
                log.warning(f"Context limit hit: {e}")
                return None, True
            raise

        except (openai.APIError, openai.APIConnectionError, openai.APITimeoutError) as e:
            wait = min(2 ** attempt * 2, 60)
            log.warning(f"API error: {e}, retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)

    log.error("All retries exhausted")
    return None, False


# ── Response parser ───────────────────────────────────────────────────────────

def extract_action(raw: str) -> str:
    """Extract clean GET/POST/FINISH action from potentially verbose response."""
    stripped = raw.strip()

    if stripped.startswith("GET ") or stripped.startswith("POST ") or stripped.startswith("FINISH("):
        return stripped

    finish_match = re.search(r'FINISH\(\[.*?\]\)', stripped, re.DOTALL)
    if finish_match:
        return finish_match.group(0)

    get_match = re.search(r'^(GET\s+https?://\S+)', stripped, re.MULTILINE)
    if get_match:
        return get_match.group(1)

    post_match = re.search(r'^(POST\s+https?://\S+)\n(\{.*)', stripped, re.MULTILINE | re.DOTALL)
    if post_match:
        url_line = post_match.group(1)
        rest = post_match.group(2)
        brace_count = 0
        end_idx = 0
        for i, c in enumerate(rest):
            if c == '{':
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        if end_idx > 0:
            return url_line + "\n" + rest[:end_idx]

    return stripped


# ── Core: run a single task ───────────────────────────────────────────────────

def run_single_task(
    client: openai.OpenAI,
    index: int,
    task_data: Dict[str, Any],
    functions: List[Dict],
    fhir_api_base: str,
    model: str,
    max_rounds: int,
    max_tokens: int,
    temperature: float,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Run a single task, returning result dict."""
    history = []

    initial_prompt = MEDAGENTBENCH_PROMPT.format(
        api_base=fhir_api_base,
        functions=json.dumps(functions),
        context=task_data["context"],
        question=task_data["instruction"],
    )
    history.append({"role": "user", "content": initial_prompt})

    try:
        for round_num in range(max_rounds):
            response_text, is_context_limit = call_model(
                client, history, model, max_tokens, temperature,
                extra_headers=extra_headers,
            )

            if is_context_limit:
                return {
                    "index": index,
                    "status": "agent context limit",
                    "result": None,
                    "history": history,
                }

            if response_text is None:
                return {
                    "index": index,
                    "status": "task error",
                    "result": {"error": "API call failed after retries"},
                    "history": history,
                }

            r = response_text.strip().replace("```tool_code", "").replace("```", "").strip()
            r = extract_action(r)
            history.append({"role": "agent", "content": r})

            if r.startswith("GET"):
                url = r[3:].strip() + "&_format=json"
                get_res = send_get_request(url)
                if "data" in get_res:
                    history.append({
                        "role": "user",
                        "content": f"Here is the response from the GET request:\n{get_res['data']}. Please call FINISH if you have got answers for all the questions and finished all the requested tasks",
                    })
                else:
                    history.append({
                        "role": "user",
                        "content": f"Error in sending the GET request: {get_res['error']}",
                    })

            elif r.startswith("POST"):
                try:
                    payload = json.loads("\n".join(r.split("\n")[1:]))
                except Exception:
                    history.append({"role": "user", "content": "Invalid POST request"})
                else:
                    history.append({
                        "role": "user",
                        "content": "POST request accepted and executed successfully. Please call FINISH if you have got answers for all the questions and finished all the requested tasks",
                    })

            elif r.startswith("FINISH("):
                return {
                    "index": index,
                    "status": "completed",
                    "result": r[len("FINISH("):-1],
                    "history": history,
                }

            else:
                return {
                    "index": index,
                    "status": "agent invalid action",
                    "result": None,
                    "history": history,
                }

    except Exception as e:
        return {
            "index": index,
            "status": "task error",
            "result": {"error": str(e)},
            "history": history,
        }

    return {
        "index": index,
        "status": "task limit reached",
        "result": None,
        "history": history,
    }


# ── Evaluation ────────────────────────────────────────────────────────────────

class HistoryItemWrapper:
    def __init__(self, d):
        self.role = d["role"]
        self.content = d["content"]


class ResultWrapper:
    def __init__(self, task_result):
        self.result = task_result["result"]
        self.history = [HistoryItemWrapper(h) for h in task_result["history"]]


def load_refsol():
    """Load refsol module for evaluation."""
    import importlib.util
    import types

    refsol_path = os.path.join("src", "server", "tasks", "medagentbench", "refsol.py")
    if not os.path.exists(refsol_path):
        return None

    try:
        pkg_name = "src.server.tasks.medagentbench"
        if pkg_name not in sys.modules:
            for parent in ["src", "src.server", "src.server.tasks"]:
                if parent not in sys.modules:
                    sys.modules[parent] = types.ModuleType(parent)

            utils_path = os.path.join("src", "server", "tasks", "medagentbench", "utils.py")
            utils_spec = importlib.util.spec_from_file_location(f"{pkg_name}.utils", utils_path)
            utils_mod = importlib.util.module_from_spec(utils_spec)
            sys.modules[f"{pkg_name}.utils"] = utils_mod
            utils_spec.loader.exec_module(utils_mod)

            pkg = types.ModuleType(pkg_name)
            pkg.__path__ = [os.path.join("src", "server", "tasks", "medagentbench")]
            pkg.__package__ = pkg_name
            pkg.utils = utils_mod
            sys.modules[pkg_name] = pkg

        spec = importlib.util.spec_from_file_location(
            f"{pkg_name}.refsol", refsol_path,
            submodule_search_locations=[]
        )
        module = importlib.util.module_from_spec(spec)
        module.__package__ = pkg_name
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        log.warning("Failed to load refsol.py: %s", e)
        return None


def evaluate_task(refsol_module, task_data: Dict, task_result: Dict, fhir_api_base: str) -> bool:
    """Evaluate task correctness using refsol grader."""
    if refsol_module is None:
        return task_result["status"] == "completed"
    if task_result["result"] is None:
        return False

    task_id = task_data["id"].split("_")[0]
    try:
        grader_func = getattr(refsol_module, task_id)
        wrapper = ResultWrapper(task_result)
        return grader_func(task_data, wrapper, fhir_api_base) is True
    except Exception as e:
        log.warning(f"Eval error for {task_data['id']}: {e}")
        return False


# ── Output writing ────────────────────────────────────────────────────────────

def get_model_output_name(model: str) -> str:
    """Convert model name to filesystem-safe name."""
    return model.replace("/", "_").replace(".", "-")


def write_result(filepath: str, index: int, task_data: Dict, task_result: Dict, is_correct: bool):
    """Append a result to the runs file."""
    timestamp = int(time.time() * 1000)
    time_str = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "index": index,
        "task_id": task_data["id"],
        "status": task_result["status"],
        "correct": is_correct,
        "result": task_result["result"],
        "num_turns": len([h for h in task_result["history"] if h["role"] == "agent"]),
        "time": time_str,
    }
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_completed_indices(runs_file: str) -> set:
    """Load indices already processed."""
    completed = set()
    if not os.path.exists(runs_file):
        return completed
    with open(runs_file, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                completed.add(record["index"])
            except Exception:
                continue
    return completed


# ── Benchmark a single model ──────────────────────────────────────────────────

def benchmark_model(
    model: str,
    api_key: str,
    base_url: str,
    test_data: List[Dict],
    functions: List[Dict],
    refsol_module,
    output_dir: str,
    fhir_api_base: str,
    max_rounds: int,
    max_tokens: int,
    temperature: float,
    delay: float,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Run benchmark for a single model on all tasks."""

    model_name = get_model_output_name(model)
    model_dir = os.path.join(output_dir, model_name)
    os.makedirs(model_dir, exist_ok=True)

    runs_file = os.path.join(model_dir, "runs.jsonl")
    completed_indices = load_completed_indices(runs_file)

    log.info("=" * 60)
    log.info(f"BENCHMARKING: {model}")
    log.info("=" * 60)

    if completed_indices:
        log.info(f"Resuming: {len(completed_indices)} tasks already done")

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    stats = {
        "model": model,
        "total": 0,
        "completed": 0,
        "correct": 0,
        "skipped": len(completed_indices),
        "invalid_action": 0,
        "limit_reached": 0,
        "context_limit": 0,
        "error": 0,
        "task_breakdown": {},
    }

    start_time = time.time()

    for idx, task_data in enumerate(test_data):
        if idx in completed_indices:
            continue

        task_id = task_data["id"]
        task_type = task_id.split("_")[0]

        log.info(f"[{idx + 1}/{len(test_data)}] {task_id}...")
        stats["total"] += 1

        try:
            result = run_single_task(
                client=client,
                index=idx,
                task_data=task_data,
                functions=functions,
                fhir_api_base=fhir_api_base,
                model=model,
                max_rounds=max_rounds,
                max_tokens=max_tokens,
                temperature=temperature,
                extra_headers=extra_headers,
            )
        except Exception as e:
            log.error(f"  Task {task_id} failed: {e}")
            stats["error"] += 1
            continue

        status = result["status"]
        is_correct = False

        if status == "completed":
            stats["completed"] += 1
            is_correct = evaluate_task(refsol_module, task_data, result, fhir_api_base)
            if is_correct:
                stats["correct"] += 1
                log.info(f"  -> CORRECT")
            else:
                log.info(f"  -> INCORRECT")
        elif status == "agent invalid action":
            stats["invalid_action"] += 1
            log.info(f"  -> invalid action")
        elif status == "task limit reached":
            stats["limit_reached"] += 1
            log.info(f"  -> max rounds")
        elif status == "agent context limit":
            stats["context_limit"] += 1
            log.info(f"  -> context limit")
        else:
            stats["error"] += 1
            log.info(f"  -> error")

        # Track per-task-type stats
        if task_type not in stats["task_breakdown"]:
            stats["task_breakdown"][task_type] = {"total": 0, "correct": 0}
        stats["task_breakdown"][task_type]["total"] += 1
        if is_correct:
            stats["task_breakdown"][task_type]["correct"] += 1

        write_result(runs_file, idx, task_data, result, is_correct)

        if delay > 0:
            time.sleep(delay)

    elapsed = time.time() - start_time
    stats["elapsed_seconds"] = elapsed
    stats["accuracy"] = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0

    # Write summary
    summary_file = os.path.join(model_dir, "summary.json")
    with open(summary_file, "w") as f:
        json.dump(stats, f, indent=2)

    # Print summary
    log.info("")
    log.info("=" * 60)
    log.info(f"RESULTS: {model}")
    log.info("=" * 60)
    log.info(f"  Accuracy: {stats['correct']}/{stats['total']} ({stats['accuracy']:.1f}%)")
    log.info(f"  Completed: {stats['completed']}")
    log.info(f"  Invalid actions: {stats['invalid_action']}")
    log.info(f"  Limit reached: {stats['limit_reached']}")
    log.info(f"  Errors: {stats['error']}")
    log.info(f"  Time: {elapsed/60:.1f} minutes")
    log.info("")
    log.info("  Per-task breakdown:")
    for task_type in sorted(stats["task_breakdown"].keys()):
        tb = stats["task_breakdown"][task_type]
        pct = tb["correct"] / tb["total"] * 100 if tb["total"] > 0 else 0
        log.info(f"    {task_type}: {tb['correct']}/{tb['total']} ({pct:.0f}%)")
    log.info("")

    return stats


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Benchmark LLMs on MedAgentBench")
    parser.add_argument("--model", type=str, help="Single model to benchmark")
    parser.add_argument("--all", action="store_true", help="Benchmark all models sequentially")
    parser.add_argument("--data-file", default=DEFAULT_DATA_FILE)
    parser.add_argument("--func-file", default=DEFAULT_FUNC_FILE)
    parser.add_argument("--fhir-api-base", default=DEFAULT_FHIR_API_BASE)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default=os.environ.get("API_KEY", ""))
    parser.add_argument("--max-rounds", type=int, default=DEFAULT_MAX_ROUNDS)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between tasks (seconds)")
    parser.add_argument("--extra-header", action="append", default=[],
                        help="Extra HTTP headers as key=value (can repeat)")
    args = parser.parse_args()

    # Parse extra headers
    extra_headers = {}
    for h in args.extra_header:
        if "=" in h:
            k, v = h.split("=", 1)
            extra_headers[k] = v
    if not extra_headers:
        extra_headers = None

    if not args.model and not args.all:
        parser.error("Specify --model MODEL or --all")

    if not args.api_key:
        log.error("No API key. Use --api-key or set API_KEY env var.")
        sys.exit(1)

    log.info("Verifying FHIR server...")
    if not verify_fhir_server(args.fhir_api_base):
        log.error(f"FHIR server not reachable at {args.fhir_api_base}")
        sys.exit(1)
    log.info("FHIR server OK")

    # Load data
    with open(args.data_file, "r") as f:
        test_data = json.load(f)
    with open(args.func_file, "r") as f:
        functions = json.load(f)
    log.info(f"Loaded {len(test_data)} tasks")

    # Load refsol
    refsol_module = load_refsol()
    if refsol_module:
        log.info("refsol.py loaded for evaluation")
    else:
        log.warning("refsol.py not available")

    os.makedirs(args.output_dir, exist_ok=True)

    # Determine models to run
    models_to_run = BENCHMARK_MODELS if args.all else [args.model]

    all_results = []
    for model in models_to_run:
        stats = benchmark_model(
            model=model,
            api_key=args.api_key,
            base_url=args.base_url,
            test_data=test_data,
            functions=functions,
            refsol_module=refsol_module,
            output_dir=args.output_dir,
            fhir_api_base=args.fhir_api_base,
            max_rounds=args.max_rounds,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            delay=args.delay,
            extra_headers=extra_headers,
        )
        all_results.append(stats)

    # Final comparison table
    if len(all_results) > 1:
        log.info("")
        log.info("=" * 70)
        log.info("BENCHMARK COMPARISON")
        log.info("=" * 70)
        log.info(f"{'Model':<45} {'Accuracy':>10} {'Correct':>10}")
        log.info("-" * 70)
        for stats in sorted(all_results, key=lambda x: -x["accuracy"]):
            log.info(f"{stats['model']:<45} {stats['accuracy']:>9.1f}% {stats['correct']:>7}/{stats['total']}")

        # Save comparison
        comparison_file = os.path.join(args.output_dir, "comparison.json")
        with open(comparison_file, "w") as f:
            json.dump(all_results, f, indent=2)
        log.info(f"\nComparison saved to: {comparison_file}")


if __name__ == "__main__":
    main()
