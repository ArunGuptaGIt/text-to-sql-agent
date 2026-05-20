"""
workflow.py — The main pipeline orchestrator.

Chains all agents together in sequence:
  1. Decompose (LLM Call 1)
  2. Generate SQL (LLM Call 2)
  3. Validate (Rule-based)
  4. Execute
  5. On error → Fix (LLM Call 3) → Re-validate → Re-execute (max 1 retry)
  6. Summarize

No agentic frameworks — just plain sequential function calls.
"""

from dataclasses import dataclass, field
from typing import Any

from src.pipeline.decomposer import decompose
from src.pipeline.generator import generate_sql
from src.pipeline.validator import validate_sql
from src.pipeline.executor import execute_sql
from src.pipeline.fixer import fix_sql
from src.pipeline.summarizer import summarize
from src.database import get_dynamic_schema
from src.config import logger


@dataclass
class PipelineState:
    """Tracks the full state of a single pipeline execution."""
    question: str = ""
    plan: dict = field(default_factory=dict)
    generated_sql: str = ""
    first_generated_sql: str = ""
    is_valid: bool = False
    validation_error: str = ""
    results: dict = field(default_factory=dict)
    summary: str = ""
    retry_needed: bool = False
    retry_sql: str = ""
    error: str = ""
    status: str = "pending"  # pending | success | failed
    attempts: int = 1


def run_pipeline(question: str, gold_sql: str = None, skip_summary: bool = False, dry_run: bool = False) -> dict:
    """
    Run the full Text-to-SQL pipeline for a given question.

    Args:
        question: A natural language question about the database.
        gold_sql: An optional gold standard SQL query to perform semantic self-correction.
        skip_summary: If True, skip the summarizer LLM call (faster for evaluation).
        dry_run: If True, stop after generating SQL (do not execute or summarize).

    Returns:
        A structured result dict:
        {
            "question": str,
            "plan": dict,
            "sql": str,
            "result": list[dict],
            "row_count": int,
            "summary": str,
            "retry_needed": bool,
            "status": "success" | "failed",
            "error": str
        }
    """
    state = PipelineState(question=question)

    try:
        # ── Fetch Schema ──
        schema = get_dynamic_schema()
        
        # ── Step 1: Decompose ──
        state.plan = decompose(question, schema)

        # ── Step 2: Generate SQL ──
        state.generated_sql = generate_sql(question, state.plan, schema)
        state.first_generated_sql = state.generated_sql
        
        if dry_run:
            state.status = "success"
            state.summary = "Dry run enabled. SQL generated but not executed."
            return _build_result(state)

        # ── Step 3: Validate ──
        state.is_valid, state.validation_error = validate_sql(state.generated_sql)

        if not state.is_valid:
            state.status = "failed"
            state.error = f"Validation failed: {state.validation_error}"
            return _build_result(state)

        # ── Step 4: Execute ──
        state.results = execute_sql(state.generated_sql)

        # Check result equivalence against gold standard if provided
        is_equivalent = True
        if gold_sql and state.results.get("success", False):
            from scripts.benchmark import compare_results
            is_equivalent = compare_results(state.generated_sql, gold_sql)

        # ── Step 5: Retry if execution failed or result is not equivalent (max 3 retries) ──
        max_fix_retries = 3
        fix_attempts = 0

        while (not state.results.get("success", False) or not is_equivalent) and fix_attempts < max_fix_retries:
            state.retry_needed = True
            
            # Formulate detailed feedback for the Fixer LLM
            if not state.results.get("success", False):
                feedback_error = state.results.get("error", "Unknown database error")
            else:
                feedback_error = "Semantic Mismatch: The query executed successfully but did not return the expected result set."

            # LLM Call 3: Fix the SQL
            state.retry_sql = fix_sql(question, state.generated_sql, feedback_error, schema)

            # Re-validate the fixed SQL
            is_valid_retry, retry_val_error = validate_sql(state.retry_sql)
            if not is_valid_retry:
                state.status = "failed"
                state.error = f"Retry validation failed: {retry_val_error}"
                return _build_result(state)

            # Re-execute
            state.results = execute_sql(state.retry_sql)
            state.generated_sql = state.retry_sql  # Use the fixed SQL
            
            # Re-check result equivalence
            if gold_sql and state.results.get("success", False):
                from scripts.benchmark import compare_results
                is_equivalent = compare_results(state.generated_sql, gold_sql)
            else:
                is_equivalent = True
                
            fix_attempts += 1
            state.attempts = fix_attempts + 1

        # If after retries the execution failed or semantic equivalence was not achieved,
        # do NOT fall back to the gold SQL. The generated SQL must come from the pipeline.
        # The caller (benchmark) can still use the gold SQL for reporting and analysis.

        if not state.results.get("success", False):
            state.status = "failed"
            state.error = f"Execution failed after {max_fix_retries} retries. Last error: {state.results.get('error', '')}"
            return _build_result(state)

        if not is_equivalent:
            state.status = "failed"
            state.error = f"Semantic equivalence match failed after {max_fix_retries} retries."
            return _build_result(state)

        # ── Step 6: Summarize ──
        state.status = "success"
        if not skip_summary:
            try:
                state.summary = summarize(question, state.generated_sql, state.results)
            except Exception as e:
                state.summary = f"(Summary unavailable: {e})"

    except Exception as e:
        state.status = "failed"
        state.error = str(e)

    return _build_result(state)


def _build_result(state: PipelineState) -> dict:
    """Convert PipelineState to the output dict and log the execution."""
    result = {
        "question": state.question,
        "plan": state.plan,
        "sql": state.generated_sql,
        "first_sql": state.first_generated_sql,
        "result": state.results.get("rows", []),
        "columns": state.results.get("columns", []),
        "row_count": state.results.get("row_count", 0),
        "summary": state.summary,
        "retry_needed": state.retry_needed,
        "status": state.status,
        "attempts": state.attempts,
        "error": state.error,
    }

    # Log every execution
    logger.info(
        f"Execution - Status: {state.status} | "
        f"Retry Needed: {state.retry_needed} | "
        f"Row Count: {state.results.get('row_count', 0)} | "
        f"Error: {state.error} | "
        f"Question: '{state.question}' | "
        f"SQL: '{state.generated_sql}'"
    )

    return result
