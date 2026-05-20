"""
validator.py — Step 3: Rule-based SQL safety validation.

No LLM involved — pure string scanning to block destructive operations.
"""

import re

# Keywords that indicate destructive / write operations
_FORBIDDEN_KEYWORDS = [
    "DELETE",
    "DROP",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
]


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate that a SQL query is read-only (SELECT only).

    Args:
        sql: The SQL query string to validate.

    Returns:
        (is_valid, error_message)
        - (True, "") if the query is safe.
        - (False, "reason") if the query contains forbidden operations.
    """
    if not sql or not sql.strip():
        return False, "Empty SQL query."

    upper_sql = sql.upper().strip()

    # Must start with SELECT or WITH (for CTEs)
    if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
        return False, f"Query must start with SELECT. Got: {upper_sql[:30]}..."

    # Check for forbidden keywords (word-boundary match to avoid false positives)
    for keyword in _FORBIDDEN_KEYWORDS:
        pattern = rf"\b{keyword}\b"
        if re.search(pattern, upper_sql):
            return False, f"Blocked: query contains forbidden keyword '{keyword}'."

    # Check for multiple statements (semicolon followed by more SQL)
    # Allow trailing semicolon but not multiple statements
    stripped = sql.strip().rstrip(";")
    if ";" in stripped:
        return False, "Blocked: multiple SQL statements detected."

    return True, ""
