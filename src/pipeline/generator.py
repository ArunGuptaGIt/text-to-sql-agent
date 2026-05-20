"""
generator.py — Step 2: Generate a PostgreSQL SELECT query from the decomposed plan.

This is LLM Call 2 in the prompt-chaining pipeline.
"""

import json
from src.llm import call_llm
from src.prompts import GENERATION_SYSTEM, GENERATION_PROMPT


def generate_sql(question: str, plan: dict, schema: str) -> str:
    """
    Generate a PostgreSQL query based on the decomposition plan.

    Args:
        question: Original natural language question.
        plan: The parsed JSON dictionary from the decomposer.
        schema: The dynamically fetched database schema.

    Returns:
        A raw string containing the PostgreSQL query.
    """
    prompt = GENERATION_PROMPT.format(
        schema=schema,
        plan=json.dumps(plan, indent=2),
        question=question,
    )

    raw_response = call_llm(prompt, system_instruction=GENERATION_SYSTEM)

    # ── Clean up response ──markdown code fences if present ──
    sql = raw_response.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(lines[1:-1]) if len(lines) > 2 else sql
    sql = sql.strip().rstrip(";") + ";"

    return sql
