"""
decomposer.py — Step 1: Break a natural language question into structured components.

This is LLM Call 1 in the prompt-chaining pipeline.
"""

import json
from src.llm import call_llm
from src.prompts import DECOMPOSITION_SYSTEM, DECOMPOSITION_PROMPT


def decompose(question: str, schema: str) -> dict:
    """
    Decompose a natural language question into structured query components.

    Args:
        question: The user's natural language question.
        schema: The dynamically fetched database schema.

    Returns:
        A dict with keys: intent, tables, columns, filters, joins, aggregations, ordering, limit.

    Raises:
        ValueError: If the LLM response cannot be parsed as JSON.
    """
    prompt = DECOMPOSITION_PROMPT.format(
        schema=schema,
        question=question,
    )

    raw_response = call_llm(prompt, system_instruction=DECOMPOSITION_SYSTEM)

    # ── Clean up response (strip markdown fences if the LLM adds them) ──
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        # Remove ```json ... ``` wrapper
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

    try:
        plan = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse decomposition response as JSON.\n"
            f"Raw response: {raw_response}\n"
            f"Error: {e}"
        )

    return plan
