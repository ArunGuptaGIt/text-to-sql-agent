"""
api/server.py — FastAPI backend for the Text-to-SQL agent.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

# Ensure the root project directory is in the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.workflow import run_pipeline

app = FastAPI(title="Text-to-SQL API", version="1.0")

class QueryRequest(BaseModel):
    question: str
    skip_summary: bool = False
    dry_run: bool = False

@app.post("/agent/sql")
def handle_sql_query(request: QueryRequest):
    """
    Execute the Text-to-SQL agent pipeline on the provided natural language question.
    """
    try:
        result = run_pipeline(
            question=request.question,
            skip_summary=request.skip_summary,
            dry_run=request.dry_run
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
