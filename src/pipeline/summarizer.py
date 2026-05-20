"""
summarizer.py — Step 6: Convert raw query results into a natural language answer.
"""

import json
from src.llm import call_llm
from src.prompts import SUMMARIZER_SYSTEM, SUMMARIZER_PROMPT


def summarize(question: str, sql: str, results: dict) -> str:
    """
    Generate a human-readable summary of the query results.

    Args:
        question: The original natural language question.
        sql: The SQL query that was executed.
        results: The result dict from the executor (columns, rows, row_count).

    Returns:
        A natural language summary string.
    """
    # Format results for the prompt (limit to first 20 rows to save tokens)
    rows_preview = results.get("rows", [])[:20]
    results_text = json.dumps(rows_preview, indent=2, default=str)

    prompt = SUMMARIZER_PROMPT.format(
        question=question,
        sql=sql,
        row_count=results.get("row_count", 0),
        results=results_text,
    )

    summary = call_llm(prompt, system_instruction=SUMMARIZER_SYSTEM)
    return summary
