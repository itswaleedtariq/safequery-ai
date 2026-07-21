# SafeQuery AI

SafeQuery AI is a secure **Text-to-SQL analytics platform** that converts natural-language business questions into validated PostgreSQL queries and database results.

The system combines schema-aware prompting, SQL guardrails, read-only execution, hallucination detection, confidence scoring, and a React dashboard.

## Features

- Natural-language business questions
- Schema-aware SQL generation with Groq
- PostgreSQL schema introspection
- SQL validation with SQLGlot
- Blocking of unsafe statements such as `INSERT`, `UPDATE`, `DELETE`, and `DROP`
- Automatic query row limits
- Dedicated read-only PostgreSQL account
- PostgreSQL `EXPLAIN` plan validation
- Query timeout and cost controls
- SQL back-translation
- Question-to-SQL alignment checking
- Business-rule validation
- Result sanity checks
- Explainable confidence scoring
- Optional multi-query agreement validation
- Automatic hiding of unsafe or low-confidence results
- React and TypeScript dashboard
- Audit logs for guardrails, execution, hallucination, confidence, and workflow decisions

## Architecture

```text
User Question
      ↓
Schema-Aware Prompt Builder
      ↓
Groq SQL Generation
      ↓
Static SQL Guardrails
      ↓
PostgreSQL EXPLAIN Validation
      ↓
Read-Only Query Execution
      ↓
Hallucination Detection
      ↓
Confidence Scoring
      ↓
React Dashboard
```

## Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Psycopg
- SQLGlot
- Groq
- Pytest

### Database

- PostgreSQL 17
- Docker Compose

### Frontend

- React
- TypeScript
- Vite
- CSS

## Database Tables

The sample e-commerce database contains:

- `categories`
- `customers`
- `products`
- `orders`
- `order_items`
- `payments`

## Project Structure

```text
safequery-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── data/
│   │   ├── db/
│   │   ├── guardrails/
│   │   ├── schemas/
│   │   └── services/
│   └── tests/
├── database/
│   └── init/
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```

## Environment Variables

Copy `.env.example` to `.env` and configure the required values.

Example:

```env
DATABASE_URL=postgresql+psycopg://safequery_admin:your_password@127.0.0.1:5433/safequery_db
READONLY_DATABASE_URL=postgresql+psycopg://safequery_reader:your_reader_password@127.0.0.1:5433/safequery_db

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MIN_CONFIDENCE_SCORE=0.65
```

Never commit the real `.env` file or API keys.

## Run Locally

### 1. Clone the repository

```powershell
git clone https://github.com/your-username/safequery-ai.git
cd safequery-ai
```

### 2. Create and activate the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create the environment file

```powershell
Copy-Item .env.example .env
```

Add your database credentials and Groq API key to `.env`.

### 5. Start PostgreSQL

```powershell
docker compose up -d
```

### 6. Start the FastAPI backend

```powershell
uvicorn backend.app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### 7. Start the React frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
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
POST /v1/hallucination/check
POST /v1/confidence/check
POST /v1/query
```

The main frontend endpoint is:

```text
POST /v1/query
```

Example request:

```json
{
  "question": "Which five products generated the highest revenue?",
  "max_tables": 4,
  "max_examples": 3,
  "run_multi_query": false
}
```

## Safety Design

Generated SQL is treated as untrusted input.

Before execution, SafeQuery AI:

1. Parses the SQL.
2. Blocks non-read-only statements.
3. Validates referenced tables and columns.
4. Applies a safe row limit when required.
5. Runs PostgreSQL `EXPLAIN`.
6. Rejects expensive query plans.
7. Executes through a dedicated read-only user.
8. Applies timeout protection.
9. Checks question alignment and business rules.
10. Calculates an explainable confidence score.

## Run Tests

Run all backend tests:

```powershell
python -m pytest backend/tests -v
```

Run specific test modules:

```powershell
python -m pytest backend/tests/test_hallucination_detector.py -v
python -m pytest backend/tests/test_confidence_scorer.py -v
python -m pytest backend/tests/test_query_workflow.py -v
```

Check Python syntax:

```powershell
python -m compileall backend
```

## Frontend Build

```powershell
cd frontend
npm run lint
npm run build
```

The production build is created in:

```text
frontend/dist/
```

## Example Questions

```text
How many customers are there?

Show the total number of completed orders.

What is the average order value?

Which five products generated the highest revenue?
```

## Current Version

```text
v1.1.0
```

## Author

**Waleed Tariq**  
Software Engineering Student