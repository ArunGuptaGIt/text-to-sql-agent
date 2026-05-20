"""
fixer.py — Step 5: Self-correction — fix broken SQL using the error message.

This is LLM Call 3 in the prompt-chaining pipeline (retry step).
"""

from src.llm import call_llm
from src.prompts import FIX_SYSTEM, FIX_PROMPT


def fix_sql(question: str, failed_sql: str, error_message: str, schema: str) -> str:
    """
    Use the LLM to fix a broken SQL query based on the database error.

    Args:
        question: The original natural language question.
        failed_sql: The SQL that failed execution.
        error_message: The exact database error message.

    Returns:
        A corrected SQL query string.
    """
    prompt = FIX_PROMPT.format(
        schema=schema,
        question=question,
        sql=failed_sql,
        error=error_message,
    )

    raw_response = call_llm(prompt, system_instruction=FIX_SYSTEM)

    # ── Clean up: strip markdown code fences if present ──
    sql = raw_response.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(lines[1:-1]) if len(lines) > 2 else sql
    sql = sql.strip().rstrip(";") + ";"

    return sql
