# 🚀 Agentic Text-to-SQL Data Pipeline

An end-to-end intelligent pipeline and agent that automatically converts natural language questions into executable SQL queries, runs them against a database, and generates human-readable summaries. It features a fully self-correcting validation and fallback loop to ensure query correctness.

## 🏗 System Architecture

The project consists of several core components working seamlessly together:

1. **User Interface (UI)**: Built with **Streamlit** (ui/app.py), providing an interactive chat interface to converse with the agent.
2. **API Backend**: A **FastAPI** application (pi/server.py) serving as a RESTful entry point to execute the core pipeline.
3. **Core Workflow (src/workflow.py)**:
   - Decomposer: Breaks down complex natural language queries into logical steps based on the dynamic database schema.
   - Generator: Constructs the SQL query leveraging the decomposition plan and schema definitions.
   - Validator: Applies rule-based checks on the generated SQL to catch obvious syntax or structural errors.
   - Executor: Runs the query against the PostgreSQL database.
   - Fixer: An LLM-powered self-correction agent that steps in when the database returns execution errors or mismatches. (Allows up to 3 automatic retries).
   - Summarizer: Converts the resulting dataset back into a conversational, human-readable summary.
4. **Benchmarking Suite**: A robust evaluation script (scripts/benchmark.py) designed to evaluate pipeline accuracy on a grounded 50-query dataset (enchmark.json). It judges queries not on string similarity, but on pure **Execution Set Equivalence** (i.e. verifying the generated query fetches the right data rows).
5. **Database Setup**: Managed via Docker (PostgreSQL 16) filled with a pre-configured classicmodels dataset (seed.sql).

## 🛠 Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [Python 3.10+](https://www.python.org/)
- API Tokens for your choice of LLM provider (HuggingFace, Gemini, etc.)

## ⚙️ Environment Configuration

1. Locate or create a .env file in the project's roots.
2. Set the following required variables:

`ini
# PostgreSQL Database (Credentials are passed seamlessly into Docker Compose)
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=classicmodels

# Note: Default internal docker connection for api container
DATABASE_URL=postgresql://admin:admin123@db:5432/classicmodels
# If testing completely manually/locally, swap the URL above to this:
# DATABASE_URL=postgresql://admin:admin123@127.0.0.1:5435/classicmodels

# LLM Selection (e.g. huggingface, gemini)
ACTIVE_LLM=huggingface

# HuggingFace Setup
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
HF_MODEL=meta-llama/Meta-Llama-3-70B-Instruct

# Gemini Setup (Optional alternative)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-lite
`

## 🚀 Running the Project

### Using Docker Compose (Recommended)

To spin up the entire application stack (Database, API, and UI Frontend) in one command:

`ash
docker-compose up --build
`
- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs (Swagger)**: http://localhost:8000/docs
- **PostgreSQL Database**: Accessible externally at localhost:5435

### Running the Evaluation Benchmark (Local)

1. Ensure your local virtual environment is active and requirements are installed:
`ash
python -m venv venv
# Enable venv on Windows:
venv\Scripts\Activate.ps1
pip install -r requirements.txt
`
2. Note: For local script executions interacting with the database, ensure DATABASE_URL in the .env file maps to the mapped localhost:5435 port as instructed above.
3. Run the benchmark tool:
`ash
cd Week3
python scripts/benchmark.py
`
4. Find the detailed generated reports in:
   - evaluation/benchmark_results.json
   - evaluation/benchmark_results.csv

## 🧠 Pipeline Error Handling
If an SQL query generation fails or hits an operational database error, the agent feeds the exception directly into a specialized Fixer LLM function, instructing it on what failed based on real database error descriptions (e.g., column not found, missing GROUP BY statement). This ensures high robustness by enabling the agent to learn from execution mistakes in a single cycle without user intervention.
