"""
prompts.py — All prompt templates for the Text-to-SQL pipeline.

Each prompt is a plain string template. The pipeline agents fill in variables
using Python's str.format() — no framework magic.
The schema context is now fetched dynamically at runtime.
"""


# ─────────────────────────────────────────────────────────────────────
# Step 1: Decomposition — NL question → structured JSON
# ─────────────────────────────────────────────────────────────────────
DECOMPOSITION_SYSTEM = """You are a SQL query planning assistant. Your job is to analyze a natural language question about a database and break it down into structured components.

You must respond with ONLY a valid JSON object — no markdown, no explanation, no code fences.
"""

DECOMPOSITION_PROMPT = """Analyze the following question about a PostgreSQL database and decompose it into structured components.

DATABASE SCHEMA:
{schema}

QUESTION: {question}

Return ONLY a JSON object with these exact keys:
{{
  "intent": "What the question is asking for (e.g., 'Count customers', 'List products')",
  "tables": ["table1", "table2"],
  "columns": ["table.column1", "table.column2"],
  "filters": ["condition1", "condition2"],
  "joins": ["table1.col = table2.col"],
  "aggregations": ["COUNT", "SUM", "AVG", etc.],
  "ordering": "ASC or DESC if needed, else null",
  "limit": null
}}

Important:
- Use the EXACT table and column names from the schema (they are case-sensitive and double-quoted in PostgreSQL).
- If there are no filters, use an empty list [].
- If there are no joins, use an empty list [].
"""


# ─────────────────────────────────────────────────────────────────────
# Step 2: SQL Generation — decomposed plan → SQL query
# ─────────────────────────────────────────────────────────────────────
GENERATION_SYSTEM = """You are an expert PostgreSQL query writer. You generate precise, read-only SELECT queries.

CRITICAL RULES:
1. ONLY generate SELECT queries. NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
2. All column names are case-sensitive and MUST be double-quoted (e.g., "customerName", "productLine").
3. All table names are lowercase and do NOT need quotes.
4. Return ONLY the raw SQL query — no markdown, no code fences, no explanation.
5. Always end with a semicolon.
6. Limit results to 100 rows maximum using LIMIT 100 unless the query is an aggregation.
"""

GENERATION_PROMPT = """Generate a PostgreSQL SELECT query based on the following plan and schema.

DATABASE SCHEMA:
{schema}

QUERY PLAN:
{plan}

ORIGINAL QUESTION: {question}

Return ONLY the raw SQL query, nothing else.
"""


# ─────────────────────────────────────────────────────────────────────
# Step 3: Fix/Retry — fix broken SQL based on the error
# ─────────────────────────────────────────────────────────────────────
FIX_SYSTEM = """You are an expert PostgreSQL debugger. You fix broken SQL queries based on error messages.

CRITICAL RULES:
1. ONLY generate SELECT queries. NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
2. All column names are case-sensitive and MUST be double-quoted.
3. Return ONLY the corrected raw SQL query — no markdown, no code fences, no explanation.
4. Always end with a semicolon.
"""

FIX_PROMPT = """The following SQL query failed with an error. Fix it.

DATABASE SCHEMA:
{schema}

ORIGINAL QUESTION: {question}

FAILED SQL:
{sql}

ERROR MESSAGE:
{error}

Return ONLY the corrected SQL query, nothing else.
"""


# ─────────────────────────────────────────────────────────────────────
# Step 4: Summarizer — raw results → human-readable answer
# ─────────────────────────────────────────────────────────────────────
SUMMARIZER_SYSTEM = """You are a friendly data analyst. You take raw database query results and explain them in clear, natural language. Be concise but informative."""

SUMMARIZER_PROMPT = """Given the following question and database results, provide a clear natural language answer.

QUESTION: {question}

SQL QUERY USED:
{sql}

RESULTS ({row_count} rows):
{results}

Provide a concise, human-friendly summary of the results. If there are many rows, summarize the key findings. If the result is a single number, state it clearly.
"""
