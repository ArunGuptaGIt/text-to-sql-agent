"""
config.py — Centralized environment variable loading.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── Paths ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ── Load .env from project root ──
_env_path = PROJECT_ROOT / ".env"
load_dotenv(_env_path)

# ── Logging Setup ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "text2sql.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("text2sql")

# ── Database ──
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin123@127.0.0.1:5432/classicmodels",
)

# ── LLM Configuration ──
ACTIVE_LLM: str = os.getenv("ACTIVE_LLM", "gemini").lower() # 'gemini' or 'huggingface'

# Gemini
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

# HuggingFace
HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
HF_MODEL: str = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3-70B-Instruct")
