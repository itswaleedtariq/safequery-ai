# SafeQuery AI

SafeQuery AI is a secure **Text-to-SQL analytics platform** that converts natural-language business questions into PostgreSQL queries.

It reduces SQL hallucinations and prevents unsafe database operations through schema-aware prompting, structured LLM output, SQL validation, and read-only execution.

## Main Features

- FastAPI backend
- PostgreSQL e-commerce database
- Automatic schema introspection
- Schema-aware prompt generation
- Structured SQL generation with Groq
- SQL safety validation with SQLGlot
- Blocking of unsafe statements such as `DELETE`, `UPDATE`, `INSERT`, and `DROP`
- Automatic row limits
- Dedicated PostgreSQL read-only user
- `EXPLAIN` plan inspection before execution
- Query timeout and cost controls
- Guardrail and execution audit logs

## Workflow

```text
User Question
      ↓
Relevant Schema Selection
      ↓
Groq SQL Generation
      ↓
SQL Safety Guardrails
      ↓
EXPLAIN Plan Validation
      ↓
Read-Only PostgreSQL Execution
      ↓
Results, SQL, Timing, and Metadata
```

## Technology Stack

- Python
- FastAPI
- PostgreSQL 17
- SQLAlchemy
- Psycopg
- Pydantic
- Groq
- SQLGlot
- Docker Compose
- Pytest

## Database Tables

- Categories
- Customers
- Products
- Orders
- Order items
- Payments

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
uvicorn backend.app.main:app --reload
```

Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

## Main API Endpoints

```text
GET  /health
GET  /health/database
GET  /v1/schema
POST /v1/prompt/preview
POST /v1/sql/generate
POST /v1/sql/validate
POST /v1/sql/execute
```

## Run Tests

```powershell
python -m pytest backend/tests -v
```

## Security

Generated SQL is treated as untrusted input. Queries are parsed, validated, limited, inspected with PostgreSQL `EXPLAIN`, and executed only through a dedicated read-only database account.

## Current Version

```text
v0.7.0
```

## Author

**Waleed Tariq**  
Software Engineering Student