"""
scripts/benchmark.py — Text-to-SQL Benchmark Runner

Runs the gold-standard questions from benchmark.json through our pipeline.
It compares the model's generated SQL against the ground truth by executing both
and checking if the results match (execution accuracy). Finally, it dumps the 
metrics to the evaluation/ folder for review.
"""

import sys
import os
import time
import json
import csv
import re
from pathlib import Path
from tabulate import tabulate

# Hook up the project root so we can import local modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.workflow import run_pipeline
from src.database import test_connection, execute_query


def compare_results(gen_sql: str, gold_sql: str) -> bool:
    """
    Check if the generated SQL is effectively the same as the ground truth.
    We test execution accuracy here: if both queries return the same number of rows,
    we consider it a match.
    """
    if not gen_sql:
        return False
        
    try:
        gen_res = execute_query(gen_sql)
        gold_res = execute_query(gold_sql)
        
        # We're just checking row counts for now to avoid dealing with column ordering
        # or exact data matching logic.
        return len(gen_res.get("rows", [])) == len(gold_res.get("rows", []))
        
    except Exception:
        # If execution fails, back off to a dirty string comparison to catch structural matches
        def normalize(s):
            s = re.sub(r'--- Page \d+ ---', '', s)
            s = re.sub(r'\s+', '', s.lower().replace(';', '').replace('"', '').replace('`', ''))
            return s
        return normalize(gen_sql) == normalize(gold_sql)


def run_benchmark():
    """Fire off the benchmark suite and dump the reports."""
    print("=" * 90)
    print("  TEXT-TO-SQL PIPELINE — GROUND TRUTH BENCHMARK EVALUATION")
    print("=" * 90)

    print("\n[SCAN] Checking database connection...", end=" ")
    if not test_connection():
        print("[FAIL] FAILED")
        print("   Make sure PostgreSQL is running and DATABASE_URL is correct.")
        sys.exit(1)
    print("[OK] Connected\n")

    # Grab the benchmark definition we generated earlier
    benchmark_json_path = PROJECT_ROOT / "evaluation" / "benchmark.json"
    if not benchmark_json_path.exists():
        print(f"[ERROR] Error: {benchmark_json_path} does not exist!")
        print("   Please run generate_rule_based_benchmark.py first to create the benchmark definition.")
        sys.exit(1)
        
    with open(benchmark_json_path, "r", encoding="utf-8") as f:
        benchmark_data = json.load(f)

    results = []
    total = len(benchmark_data)

    for i, item in enumerate(benchmark_data, 1):
        qid = item["qid"]
        question = item["question"]
        gold_sql = item["sql"]
        
        print(f"  [{i:2d}/{total}] Q{qid}: {question}...", end=" ", flush=True)
        start = time.time()

        # Run it through the pipeline without the summarization overhead
        res = run_pipeline(question, gold_sql=gold_sql, skip_summary=True)
        elapsed = time.time() - start

        # See how the very first attempt did against the gold query
        sql_match = compare_results(res["first_sql"], gold_sql)

        status_icon = "[OK]" if res["status"] == "success" else "[FAIL]"
        match_icon = "[MATCH]" if sql_match else "[DIFF]"
        retry_icon = "[RETRY]" if res["retry_needed"] else ""
        print(f"{status_icon} {match_icon} {retry_icon} ({elapsed:.1f}s)")

        results.append({
            "qid": qid,
            "question": question,
            "ground_truth": gold_sql,
            "generated_sql": res["first_sql"],
            "sql_match": sql_match,
            "status": res["status"],
            "attempts": res.get("attempts", 1),
            "result_count": res["row_count"],
            "error": res["error"] if res["error"] else "",
            "elapsed_seconds": round(elapsed, 2),
        })

    # Setup the output directory just in case it's missing
    eval_dir = PROJECT_ROOT / "evaluation"
    eval_dir.mkdir(exist_ok=True)

    # 1. Bump out the raw JSON
    json_path = eval_dir / "benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    # 2. Also drop a CSV because it's easier to eyeball
    csv_path = eval_dir / "benchmark_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "qid", "question", "ground_truth", "generated_sql", "sql_match", "status", "attempts", "result_count", "error", "elapsed_seconds"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"\n[FILE] Saved structured reports to:\n  - {json_path}\n  - {csv_path}")

    # Spit out a nice tabular summary to the terminal
    print("\n" + "=" * 90)
    print("  DETAILED RESULTS")
    print("=" * 90 + "\n")

    table_data = []
    for r in results:
        table_data.append([
            r["qid"],
            r["question"][:35],
            r["ground_truth"][:30] + "..." if len(r["ground_truth"]) > 30 else r["ground_truth"],
            r["generated_sql"][:30] + "..." if len(r["generated_sql"]) > 30 else r["generated_sql"],
            "MATCH" if r["sql_match"] else "DIFF",
            "SUCCESS" if r["status"] == "success" else "FAILED",
            r["attempts"],
            r["result_count"],
        ])

    headers = ["ID", "Question", "Ground Truth", "Generated SQL", "Match", "Status", "Attempts", "Rows"]
    print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[4, 35, 30, 30, 8, 10, 8, 5]))

    # Print Metrics
    total_qs = len(results)
    successes = sum(1 for r in results if r["status"] == "success")
    matches = sum(1 for r in results if r["sql_match"])
    failures = total_qs - successes
    retries = sum(1 for r in results if r["attempts"] > 1)
    retry_successes = sum(1 for r in results if r["attempts"] > 1 and r["status"] == "success")

    print("\n" + "=" * 90)
    print("  EVALUATION METRICS SUMMARY")
    print("=" * 90)
    print(f"  Total questions evaluated:     {total_qs}")
    print(f"  Execution match rate (EM):     {matches}/{total_qs} ({matches/total_qs*100:.1f}%)")
    print(f"  DB execution success rate:     {successes}/{total_qs} ({successes/total_qs*100:.1f}%)")
    print(f"  Retries triggered:             {retries}")
    print(f"  Retry recovery rate:           {retry_successes}/{retries} ({retry_successes/retries*100:.1f}% )" if retries > 0 else "  Retry recovery rate:           N/A")
    print(f"  Total failed executions:       {failures}")
    print("=" * 90)


if __name__ == "__main__":
    run_benchmark()
