# SafeQuery AI

SafeQuery AI is a secure, schema-aware natural-language-to-SQL platform.

The final system will allow users to ask business questions in plain English, translate those questions into PostgreSQL queries, validate the generated SQL with safety guardrails, execute approved queries using read-only database permissions, detect possible hallucinations, and return results with an explainable confidence score.

## Current Project Status

Completed milestones:

- Milestone 1: FastAPI project setup and GitHub initialization
- Milestone 2: PostgreSQL schema, Docker setup, sample data, and verification queries
- Milestone 3: SQLAlchemy connection and automatic schema introspection
- Milestone 4: Schema-aware relevance filtering and prompt construction

Current version:

```text
v0.4.0
```

The project can now:

- Connect FastAPI to PostgreSQL
- Inspect the database structure automatically
- Identify relevant tables for a natural-language question
- Detect business terms such as revenue and order value
- Add relationship bridge tables when required
- Select verified question-to-SQL examples
- Detect ambiguous questions
- Construct a focused Text-to-SQL prompt

The project does not generate or execute LLM-produced SQL yet. Structured SQL generation will be added in Milestone 5.

---

## Project Goal

SafeQuery AI is designed to answer business questions such as:

```text
Which five products generated the highest revenue?

Show revenue by shipping city.

What is the average order value by customer city?

How many completed orders were placed in June 2026?

How many active products are in each category?

Show customers who placed more than three orders.
```

The final system will return:

- Generated PostgreSQL
- Plain-English SQL explanation
- Query results
- Tables and columns used
- Safety warnings
- Hallucination warnings
- Confidence score
- Query history
- User feedback controls

---

## Current Architecture

```text
User Question
      |
      v
FastAPI
      |
      v
Schema-Aware Prompt Engine
      |
      +--> Business Term Detection
      |
      +--> Relevant Table Selection
      |
      +--> Relationship Bridge Discovery
      |
      +--> Few-Shot Example Selection
      |
      +--> Ambiguity Detection
      |
      v
Prompt Preview
```

Database layer:

```text
Docker Compose
      |
      v
PostgreSQL 17
      |
      v
E-commerce Database
      |
      +-- categories
      +-- customers
      +-- products
      +-- orders
      +-- order_items
      +-- payments
```

Future architecture:

```text
User Question
      |
      v
Schema-Aware Prompt Engine
      |
      v
LLM SQL Generator
      |
      v
SQL Syntax Validator
      |
      v
Safety Guardrails
      |
      v
Read-Only PostgreSQL Executor
      |
      v
Hallucination and Result Validator
      |
      v
Confidence Score
      |
      v
Results + SQL + Explanation
```

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Backend API | FastAPI |
| ASGI Server | Uvicorn |
| Validation | Pydantic |
| Settings | Pydantic Settings |
| Database | PostgreSQL 17 |
| Database Toolkit | SQLAlchemy |
| PostgreSQL Driver | Psycopg 3 |
| Containerization | Docker and Docker Compose |
| Data Processing | Pandas |
| Testing | Pytest |
| Version Control | Git and GitHub |
| Planned LLM Provider | Groq |
| Planned SQL Parsing | SQLGlot and SQLParse |

---

## Project Structure

```text
safequery-ai/
├── backend/
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── prompt.py
│   │   │   ├── router.py
│   │   │   └── schema.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── business_glossary.json
│   │   │   └── few_shot_examples.json
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── session.py
│   │   ├── guardrails/
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── database_schema.py
│   │   │   └── prompt_context.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── prompt_builder.py
│   │   │   └── schema_introspection.py
│   │   ├── validators/
│   │   │   └── __init__.py
│   │   └── main.py
│   └── tests/
│       ├── __init__.py
│       ├── test_prompt_builder.py
│       └── test_schema_introspection.py
│
├── database/
│   ├── init/
│   │   ├── 01_schema.sql
│   │   └── 02_seed.sql
│   └── queries/
│       └── verification.sql
│
├── docs/
│   └── business_glossary.md
│
├── evals/
├── frontend/
├── .env.example
├── .gitignore
├── compose.yaml
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Database Schema

SafeQuery AI currently uses a reproducible e-commerce analytics database.

### Categories

Stores product categories.

Important columns:

```text
id
name
description
```

### Customers

Stores customer information.

Important columns:

```text
id
full_name
email
city
country
created_at
```

### Products

Stores the product catalog.

Important columns:

```text
id
category_id
name
sku
price
stock_quantity
active
created_at
```

Relationship:

```text
products.category_id → categories.id
```

### Orders

Stores customer orders.

Important columns:

```text
id
customer_id
order_date
status
shipping_city
total_amount
created_at
```

Relationship:

```text
orders.customer_id → customers.id
```

Supported order statuses:

```text
pending
shipped
completed
cancelled
```

### Order Items

Stores products included in each order.

Important columns:

```text
id
order_id
product_id
quantity
unit_price
line_total
```

Relationships:

```text
order_items.order_id → orders.id
order_items.product_id → products.id
```

The `line_total` column is generated automatically:

```text
line_total = quantity × unit_price
```

### Payments

Stores payment information.

Important columns:

```text
id
order_id
payment_date
amount
method
status
created_at
```

Relationship:

```text
payments.order_id → orders.id
```

Supported payment methods:

```text
card
bank_transfer
cash_on_delivery
digital_wallet
```

Supported payment statuses:

```text
pending
completed
failed
refunded
```

---

## Sample Dataset

The database initialization scripts create:

| Table | Records |
|---|---:|
| Categories | 8 |
| Customers | 500 |
| Products | 100 |
| Orders | 2,000 |
| Order items | 4,000 |
| Payments | 2,000 |

The seed script uses a fixed date anchor so query results remain consistent across:

- Local development
- Automated tests
- GitHub Actions
- Deployment environments

---

## Business Definitions

The human-readable glossary is stored in:

```text
docs/business_glossary.md
```

The machine-readable glossary is stored in:

```text
backend/app/data/business_glossary.json
```

### Revenue

Revenue is calculated from:

```text
order_items.line_total
```

Only orders with these statuses are included:

```text
completed
shipped
```

Pending and cancelled orders are excluded.

### Order Value

Order value is stored in:

```text
orders.total_amount
```

It represents the sum of all related item line totals.

### Customer City

The customer home city is stored in:

```text
customers.city
```

### Shipping City

The order destination city is stored in:

```text
orders.shipping_city
```

Customer city and shipping city may be different.

### Successful Payment

A successful payment has:

```text
payments.status = 'completed'
```

### Active Product

An active product has:

```text
products.active = true
```

### Historical Product Price

The current catalog price is stored in:

```text
products.price
```

The price at the time an order was placed is stored in:

```text
order_items.unit_price
```

Revenue calculations should use the historical order price or `line_total`, not the current catalog price.

---

## Milestone 3: Database Schema Introspection

The FastAPI backend connects to PostgreSQL using SQLAlchemy and automatically extracts the database structure.

The schema introspection service discovers:

- Table names
- Table descriptions
- Column names
- Data types
- Nullable fields
- Default values
- Primary keys
- Foreign keys
- Table relationships
- Indexes
- Computed columns
- Low-cardinality sample values

The schema response is generated directly from PostgreSQL and is not hardcoded.

### Database Health Endpoint

```text
GET /health/database
```

Example response:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Schema Endpoint

```text
GET /v1/schema
```

Force a fresh inspection:

```text
GET /v1/schema?refresh=true
```

Example response structure:

```json
{
  "database_name": "safequery_db",
  "schema_name": "public",
  "table_count": 6,
  "tables": [
    {
      "name": "orders",
      "primary_key_columns": ["id"],
      "columns": [],
      "foreign_keys": [],
      "indexes": []
    }
  ]
}
```

---

## Milestone 4: Schema-Aware Prompt Engine

SafeQuery AI now transforms a natural-language business question into focused context for future SQL generation.

The prompt engine performs:

- Business terminology detection
- Table relevance scoring
- Column-name matching
- Table-description matching
- Sample-value matching
- Foreign-key graph construction
- Relationship bridge-table discovery
- Relevant relationship extraction
- Few-shot example selection
- Ambiguity detection
- Dynamic Text-to-SQL prompt construction

### Why Schema Filtering Matters

Sending the entire schema for every question can:

- Waste LLM context
- Increase cost
- Confuse the model
- Increase hallucination risk
- Reduce SQL accuracy

The prompt engine selects only the tables and relationships required for the question.

Example:

```text
Question:
Which five products generated the highest revenue?
```

Relevant tables:

```text
products
order_items
orders
```

Relevant relationship path:

```text
products.id → order_items.product_id
orders.id → order_items.order_id
```

Detected business term:

```text
revenue
```

### Bridge-Table Discovery

Some concepts are not connected directly.

Example:

```text
Show completed payments by customer city.
```

The main tables are:

```text
payments
customers
```

They require the bridge table:

```text
payments → orders → customers
```

The prompt engine discovers and adds `orders` automatically.

### Ambiguity Detection

The system asks for clarification when a question has multiple valid interpretations.

Example:

```text
Show revenue by city.
```

The database contains:

```text
customers.city
orders.shipping_city
```

Instead of guessing, the system returns clarification options.

---

## Few-Shot Examples

Verified question-to-SQL examples are stored in:

```text
backend/app/data/few_shot_examples.json
```

Current examples include:

- Top products by revenue
- Revenue by shipping city
- Average order value by customer city
- Completed orders in June 2026
- Active products by category
- Customers with more than three orders

These examples help the future LLM follow:

- Database relationships
- Business definitions
- PostgreSQL syntax
- Query style
- Expected filters

---

## API Endpoints

### Application Health

```text
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "project": "SafeQuery AI"
}
```

### Database Health

```text
GET /health/database
```

Example response:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Database Schema

```text
GET /v1/schema
```

Optional refresh:

```text
GET /v1/schema?refresh=true
```

### Prompt Preview

```text
POST /v1/prompt/preview
```

Example request:

```json
{
  "question": "Which five products generated the highest revenue?",
  "max_tables": 4,
  "max_examples": 3
}
```

The endpoint returns:

- Original question
- Selected tables
- Relevance scores
- Selection reasons
- Included columns
- Selected relationships
- Detected business terms
- Selected few-shot examples
- Clarification status
- Complete future LLM prompt

This endpoint does not call an LLM and does not execute SQL.

---

## Example Prompt Preview Request

```powershell
$body = @{
    question = "Which five products generated the highest revenue?"
    max_tables = 4
    max_examples = 3
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/v1/prompt/preview" `
    -ContentType "application/json" `
    -Body $body
```

Display selected tables:

```powershell
$response.selected_tables.name
```

Display detected business terms:

```powershell
$response.business_terms.term
```

Display the final prompt:

```powershell
$response.prompt
```

---

## Prerequisites

Install:

- Python 3.11 or newer
- Git
- Docker Desktop
- Visual Studio Code

Verify installations:

```powershell
python --version
git --version
docker --version
docker compose version
```

Docker Desktop must be open and the Linux container engine must be running.

---

## Local Setup

### 1. Clone the repository

```powershell
git clone https://github.com/itswaleedtariq/safequery-ai.git
cd safequery-ai
```

### 2. Create the virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create the local environment file

Copy `.env.example` and create `.env`.

Recommended local configuration:

```env
APP_NAME=SafeQuery AI
APP_ENV=development
DEBUG=true

POSTGRES_DB=safequery_db
POSTGRES_USER=safequery_admin
POSTGRES_PASSWORD=safequery_admin_password
POSTGRES_PORT=5433

DATABASE_URL=postgresql+psycopg://safequery_admin:safequery_admin_password@127.0.0.1:5433/safequery_db
DATABASE_SCHEMA=public

SCHEMA_SAMPLE_LIMIT=5
SCHEMA_CATEGORICAL_MAX_DISTINCT=25

GROQ_API_KEY=

MAX_RESULT_ROWS=1000
QUERY_TIMEOUT_SECONDS=10
MIN_CONFIDENCE_SCORE=0.65
```

The `.env` file contains local secrets and must not be committed.

Confirm Git ignores it:

```powershell
git check-ignore .env
```

Expected:

```text
.env
```

---

## Docker and PostgreSQL

### Validate Docker Compose

```powershell
docker compose config
```

### Start PostgreSQL

```powershell
docker compose up -d
```

### Check status

```powershell
docker compose ps
```

Expected host-to-container port mapping:

```text
0.0.0.0:5433->5432/tcp
```

### View logs

```powershell
docker compose logs -f postgres
```

Press `Ctrl + C` to stop viewing logs.

### Connect with psql

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db
```

List tables:

```sql
\dt
```

Exit:

```sql
\q
```

---

## Verify Database Records

Run the verification script:

```powershell
Get-Content database\queries\verification.sql |
    docker compose exec -T postgres `
    psql -U safequery_admin -d safequery_db
```

Verify order count:

```powershell
docker compose exec postgres `
    psql -U safequery_admin -d safequery_db `
    -c "SELECT COUNT(*) FROM orders;"
```

Expected:

```text
2000
```

---

## Run the FastAPI Application

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start the API:

```powershell
uvicorn backend.app.main:app --reload
```

Application health:

```text
http://127.0.0.1:8000/health
```

Database health:

```text
http://127.0.0.1:8000/health/database
```

Schema endpoint:

```text
http://127.0.0.1:8000/v1/schema
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Testing

The project uses Pytest.

The project root is added to the Python import path through:

```text
pytest.ini
```

Run all tests:

```powershell
python -m pytest backend/tests -v
```

Current test coverage includes:

- Expected database tables
- Foreign-key relationships
- Computed `line_total` column
- Revenue question table selection
- Business-term detection
- Ambiguous city clarification
- Clear shipping-city handling
- Prompt safety rules
- Relationship bridge-table discovery

PostgreSQL must be running while integration tests execute.

---

## Test Schema Introspection Directly

```powershell
python -c "from backend.app.services.schema_introspection import introspect_database_schema; s=introspect_database_schema(); print(s.database_name, s.table_count)"
```

Expected:

```text
safequery_db 6
```

List table names:

```powershell
python -c "from backend.app.services.schema_introspection import introspect_database_schema; print([table.name for table in introspect_database_schema().tables])"
```

Expected:

```text
['categories', 'customers', 'order_items', 'orders', 'payments', 'products']
```

---

## Test Prompt Construction Directly

```powershell
python -c "from backend.app.schemas.prompt_context import PromptPreviewRequest; from backend.app.services.prompt_builder import build_prompt_preview; r=build_prompt_preview(PromptPreviewRequest(question='Which five products generated the highest revenue?')); print([t.name for t in r.selected_tables])"
```

Expected tables include:

```text
products
order_items
orders
```

Test business terms:

```powershell
python -c "from backend.app.schemas.prompt_context import PromptPreviewRequest; from backend.app.services.prompt_builder import build_prompt_preview; r=build_prompt_preview(PromptPreviewRequest(question='Which five products generated the highest revenue?')); print([t.term for t in r.business_terms])"
```

Expected:

```text
['revenue']
```

Test ambiguity handling:

```powershell
python -c "from backend.app.schemas.prompt_context import PromptPreviewRequest; from backend.app.services.prompt_builder import build_prompt_preview; r=build_prompt_preview(PromptPreviewRequest(question='Show revenue by city')); print(r.requires_clarification); print(r.clarification_message)"
```

Expected:

```text
True
```

---

## Database Persistence

PostgreSQL data is stored in the Docker named volume:

```text
safequery-ai_safequery_postgres_data
```

Stopping Docker does not remove database data.

Stop services:

```powershell
docker compose down
```

Start again:

```powershell
docker compose up -d
```

Do not use `-v` unless you intentionally want to delete and recreate the database.

---

## Reset the Development Database

The SQL initialization scripts run only when PostgreSQL starts with an empty data volume.

After modifying `01_schema.sql` or `02_seed.sql`, reset the database:

```powershell
docker compose down -v
docker compose up -d
```

Warning:

```text
docker compose down -v
```

deletes the local PostgreSQL data volume.

The sample database will be recreated from the initialization scripts.

---

## Common Problems

### Docker engine is not running

Error:

```text
failed to connect to the docker API
dockerDesktopLinuxEngine
```

Solution:

1. Open Docker Desktop.
2. Wait until the engine starts.
3. Confirm Linux containers are enabled.
4. Run:

```powershell
docker info
docker compose up -d
```

### PostgreSQL port mismatch

The current local configuration uses:

```text
Windows host port: 5433
Container PostgreSQL port: 5432
```

Check:

```powershell
docker compose ps
```

Expected:

```text
0.0.0.0:5433->5432/tcp
```

The database URL must use port `5433`:

```env
DATABASE_URL=postgresql+psycopg://safequery_admin:safequery_admin_password@127.0.0.1:5433/safequery_db
```

### Password authentication failed

Reset the PostgreSQL role password:

```powershell
docker compose exec postgres `
    psql -U safequery_admin -d safequery_db `
    -c "ALTER ROLE safequery_admin WITH LOGIN PASSWORD 'safequery_admin_password';"
```

### Database connection returns `False`

Check:

```powershell
docker compose ps
```

Then verify the loaded settings:

```powershell
python -c "from backend.app.core.config import get_settings; print(get_settings().database_url)"
```

Test directly:

```powershell
python -c "import psycopg; conn=psycopg.connect(host='127.0.0.1', port=5433, dbname='safequery_db', user='safequery_admin', password='safequery_admin_password'); print(conn.execute('SELECT current_database(), current_user').fetchone()); conn.close()"
```

### Pytest cannot import `backend`

Ensure these files exist:

```text
backend/__init__.py
backend/tests/__init__.py
pytest.ini
```

Run tests with:

```powershell
python -m pytest backend/tests -v
```

### JSON configuration error

Validate the business glossary:

```powershell
python -m json.tool backend/app/data/business_glossary.json
```

Validate few-shot examples:

```powershell
python -m json.tool backend/app/data/few_shot_examples.json
```

### Prompt data file not found

Check:

```powershell
Get-ChildItem backend\app\data
```

Expected:

```text
__init__.py
business_glossary.json
few_shot_examples.json
```

---

## Security Notes

The current database account is an administrative development account.

Before generated SQL is executed, the project will add:

- Application-level SQL guardrails
- Single-statement validation
- Read-only query enforcement
- Row limits
- Query timeouts
- Table and column validation
- PostgreSQL SELECT-only permissions
- Query audit logs

Private API keys and database credentials must never be committed to GitHub.

---

## Planned Next Milestone

### Milestone 5: Structured SQL Generation

The next milestone will connect the prompt engine to Groq.

The LLM will return structured data containing:

- Generated PostgreSQL
- Plain-English explanation
- Tables used
- Columns used
- Model confidence
- Clarification status

Generated SQL will not be executed until the safety guardrail milestone is complete.

---

## Roadmap

- [x] Milestone 1: Project initialization
- [x] Milestone 2: PostgreSQL schema and sample data
- [x] Milestone 3: Database connection and schema introspection
- [x] Milestone 4: Schema-aware prompt engine
- [ ] Milestone 5: Structured SQL generation
- [ ] Milestone 6: SQL safety guardrails
- [ ] Milestone 7: Read-only execution layer
- [ ] Milestone 8: Hallucination detection
- [ ] Milestone 9: Confidence scoring
- [ ] Milestone 10: Complete FastAPI query workflow
- [ ] Milestone 11: Frontend dashboard
- [ ] Milestone 12: Evaluation dataset and metrics
- [ ] Milestone 13: Automated tests and GitHub Actions
- [ ] Milestone 14: Full Dockerization
- [ ] Milestone 15: Deployment
- [ ] Milestone 16: Portfolio polish

---

## Author

**Waleed Tariq**

Software Engineering Student

GitHub:

```text
https://github.com/itswaleedtariq
```