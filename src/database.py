"""
database.py — Database connection and query execution using SQLAlchemy.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from src.config import DATABASE_URL


# ── Engine (singleton, connection-pooled) ──
_engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)


@contextmanager
def get_connection():
    """Yield a raw DBAPI connection, auto-committed on success."""
    conn = _engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(sql: str) -> dict:
    """
    Execute a SELECT query and return results.

    Returns:
        {
            "columns": ["col1", "col2", ...],
            "rows": [{"col1": val, "col2": val}, ...],
            "row_count": int
        }

    Raises:
        SQLAlchemyError on any database error.
    """
    with get_connection() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }


def test_connection() -> bool:
    """Quick health-check: returns True if DB is reachable."""
    try:
        with get_connection() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False

def get_dynamic_schema() -> str:
    """
    Dynamically inspects the database and returns a minified schema string.
    Format: Table tablename (col1, col2, ...)
    """
    try:
        query = """
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        ORDER BY table_name, ordinal_position;
        """
        result = execute_query(query)
        
        tables = {}
        for row in result["rows"]:
            t_name = row["table_name"]
            c_name = row["column_name"]
            if t_name not in tables:
                tables[t_name] = []
            tables[t_name].append(c_name)
            
        schema_lines = []
        for t_name, cols in tables.items():
            schema_lines.append(f"Table {t_name} ({', '.join(cols)})")
            
        return "\n".join(schema_lines)
    except Exception as e:
        from src.config import logger
        logger.error(f"Failed to fetch dynamic schema: {e}")
        return ""
