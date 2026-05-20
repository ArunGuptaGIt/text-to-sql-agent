"""
executor.py — Step 4: Execute validated SQL against PostgreSQL.
"""

from src.database import execute_query


def execute_sql(sql: str) -> dict:
    """
    Execute a validated SQL query and return results.

    Args:
        sql: A validated SELECT query string.

    Returns:
        {
            "columns": [...],
            "rows": [...],
            "row_count": int,
            "success": True
        }

    Raises:
        Exception: Any database error (syntax, missing column, etc.)
    """
    try:
        result = execute_query(sql)
        result["success"] = True
        return result
    except Exception as e:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "success": False,
            "error": str(e),
        }
