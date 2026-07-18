# SafeQuery AI

SafeQuery AI is a secure natural-language-to-SQL analytics platform.

The final system will allow users to ask business questions in plain English, convert those questions into PostgreSQL queries, validate the generated SQL through safety guardrails, execute it using read-only permissions, detect possible hallucinations, and return results with an explainable confidence score.

## Current Project Status

Completed milestones:

- Milestone 1: FastAPI project setup and GitHub initialization
- Milestone 2: PostgreSQL database, relational schema, Docker setup, sample data, and verification queries

Current version:

```text
v0.2.0
```

The AI-based SQL generation functionality will be added in later milestones.

---

## Current Architecture

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

The FastAPI backend currently includes a health endpoint. Database integration with the backend will be added in Milestone 3.

---

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3.11+ |
| API Framework | FastAPI |
| ASGI Server | Uvicorn |
| Database | PostgreSQL 17 |
| Database Driver | Psycopg |
| Database Toolkit | SQLAlchemy |
| Containerization | Docker and Docker Compose |
| Data Processing | Pandas |
| Testing | Pytest |
| Version Control | Git and GitHub |
| Planned LLM Provider | Groq |

---

## Project Structure

```text
safequery-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── guardrails/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── validators/
│   │   ├── __init__.py
│   │   └── main.py
│   └── tests/
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
├── requirements.txt
└── README.md
```

---

## Milestone 2 Overview

Milestone 2 creates the relational database that SafeQuery AI will query in later milestones.

The database represents an e-commerce business and supports realistic analytical questions such as:

```text
Which five products generated the highest revenue?

Which shipping city produced the most revenue?

What is the average order value by customer city?

Which product category generated the most sales?

How many completed orders were placed during a specific period?
```

The database includes enough relationships to test:

- Single-table queries
- Multi-table joins
- Aggregations
- Grouping
- Sorting
- Date filtering
- Business rules
- Foreign-key relationships

---

## Database Schema

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

Stores individual products included in each order.

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

Stores payment information for orders.

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

The initialization scripts create the following records:

| Table | Records |
|---|---:|
| Categories | 8 |
| Customers | 500 |
| Products | 100 |
| Orders | 2,000 |
| Order items | 4,000 |
| Payments | 2,000 |

The seed script uses a fixed date anchor instead of the current date. This keeps query results consistent across local development, automated tests, GitHub Actions, and deployment environments.

---

## Business Definitions

The business glossary is stored in:

```text
docs/business_glossary.md
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

### Historical Product Price

```text
products.price
```

represents the current catalog price.

```text
order_items.unit_price
```

represents the product price at the time an order was placed.

Revenue calculations must use:

```text
order_items.unit_price
```

### Customer City

The customer’s home city is stored in:

```text
customers.city
```

### Shipping City

The order destination is stored in:

```text
orders.shipping_city
```

Customer city and shipping city may be different.

### Successful Payment

A successful payment has:

```text
payments.status = 'completed'
```

---

## Prerequisites

Install the following software before running the project:

- Python 3.11 or newer
- Git
- Docker Desktop
- Visual Studio Code

Verify the installations:

```powershell
python --version
git --version
docker --version
docker compose version
```

Docker Desktop must be open and the Docker Linux engine must be running.

---

## Local Setup

### 1. Clone the repository

```powershell
git clone https://github.com/itswaleedtariq/safequery-ai.git
cd safequery-ai
```

### 2. Create the Python virtual environment

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

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create the local environment file

Copy:

```text
.env.example
```

and create:

```text
.env
```

Example local configuration:

```env
APP_NAME=SafeQuery AI
APP_ENV=development
DEBUG=true

POSTGRES_DB=safequery_db
POSTGRES_USER=safequery_admin
POSTGRES_PASSWORD=safequery_admin_password
POSTGRES_PORT=5432

DATABASE_URL=postgresql+psycopg://safequery_admin:safequery_admin_password@localhost:5432/safequery_db

GROQ_API_KEY=

MAX_RESULT_ROWS=1000
QUERY_TIMEOUT_SECONDS=10
MIN_CONFIDENCE_SCORE=0.65
```

The `.env` file contains private local settings and must not be committed to GitHub.

Confirm that Git ignores it:

```powershell
git check-ignore .env
```

Expected output:

```text
.env
```

---

## Running PostgreSQL

### Validate the Docker Compose configuration

```powershell
docker compose config
```

This checks the Compose file and resolves environment variables.

### Start PostgreSQL

```powershell
docker compose up -d
```

### Check container status

```powershell
docker compose ps
```

Expected status:

```text
safequery-postgres    Up (healthy)
```

During the first startup, Docker may take several seconds to download the PostgreSQL image and initialize the database.

### View PostgreSQL logs

```powershell
docker compose logs -f postgres
```

Press:

```text
Ctrl + C
```

to stop viewing the logs. This does not stop the database.

---

## Connecting to PostgreSQL

Open the PostgreSQL command-line client:

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db
```

The terminal should change to:

```text
safequery_db=#
```

List the tables:

```sql
\dt
```

Inspect the `orders` table:

```sql
\d orders
```

Inspect the `order_items` table:

```sql
\d order_items
```

Exit PostgreSQL:

```sql
\q
```

---

## Verifying the Database

Run the complete verification script:

```powershell
Get-Content database\queries\verification.sql | docker compose exec -T postgres psql -U safequery_admin -d safequery_db
```

The verification script checks:

- Record counts
- Top products by revenue
- Revenue by shipping city
- Average order value by customer city
- Order status distribution
- Revenue by category

### Verify record counts individually

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db -c "SELECT COUNT(*) FROM categories;"
```

Expected:

```text
8
```

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db -c "SELECT COUNT(*) FROM customers;"
```

Expected:

```text
500
```

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db -c "SELECT COUNT(*) FROM products;"
```

Expected:

```text
100
```

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db -c "SELECT COUNT(*) FROM orders;"
```

Expected:

```text
2000
```

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db -c "SELECT COUNT(*) FROM order_items;"
```

Expected:

```text
4000
```

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db -c "SELECT COUNT(*) FROM payments;"
```

Expected:

```text
2000
```

---

## Example Business Query

The following query returns the five products with the highest revenue:

```sql
SELECT
    products.name,
    ROUND(
        SUM(order_items.line_total),
        2
    ) AS revenue
FROM products
JOIN order_items
    ON order_items.product_id = products.id
JOIN orders
    ON orders.id = order_items.order_id
WHERE orders.status IN ('completed', 'shipped')
GROUP BY
    products.id,
    products.name
ORDER BY revenue DESC
LIMIT 5;
```

Later, SafeQuery AI will generate this type of SQL from a natural-language question:

```text
Which five products generated the highest revenue?
```

---

## Database Persistence

PostgreSQL data is stored in a Docker named volume:

```text
safequery-ai_safequery_postgres_data
```

Stopping the container does not remove the database data.

Stop the database:

```powershell
docker compose down
```

Start it again:

```powershell
docker compose up -d
```

Verify persistence:

```powershell
docker compose exec postgres psql -U safequery_admin -d safequery_db -c "SELECT COUNT(*) FROM orders;"
```

Expected:

```text
2000
```

---

## Resetting the Development Database

The initialization scripts inside:

```text
database/init/
```

run only when PostgreSQL starts with a new, empty data volume.

After changing `01_schema.sql` or `02_seed.sql`, reset the database:

```powershell
docker compose down -v
docker compose up -d
```

Warning:

```text
docker compose down -v
```

deletes the current local PostgreSQL volume and all stored data.

This is acceptable for the development database because the seed script recreates the sample dataset.

---

## Running the FastAPI Application

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start the API:

```powershell
uvicorn backend.app.main:app --reload
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Expected health response:

```json
{
  "status": "healthy",
  "project": "SafeQuery AI"
}
```

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
2. Wait until the Docker engine is running.
3. Confirm Docker is using Linux containers.
4. Run:

```powershell
docker info
docker compose up -d
```

If Docker Desktop remains unavailable:

```powershell
wsl --shutdown
```

Restart Docker Desktop and try again.

### PostgreSQL port 5432 is already in use

Change `.env`:

```env
POSTGRES_PORT=5433
```

Update the database URL:

```env
DATABASE_URL=postgresql+psycopg://safequery_admin:safequery_admin_password@localhost:5433/safequery_db
```

Restart the service:

```powershell
docker compose down
docker compose up -d
```

### PostgreSQL container is unhealthy

Inspect the logs:

```powershell
docker compose logs postgres
```

### Updated SQL files are not being applied

Reset the database volume:

```powershell
docker compose down -v
docker compose up -d
```

### Environment file is accidentally visible to Git

Check:

```powershell
git status
git check-ignore .env
```

The `.env` file must be ignored.

---

## Milestone 2 Completion Criteria

Milestone 2 is complete when:

- PostgreSQL runs successfully through Docker
- The container reports a healthy status
- All six tables exist
- All expected sample records exist
- Foreign-key relationships work
- Order totals match order item totals
- Revenue aggregation queries work
- Data persists after restarting the container
- The `.env` file is ignored by Git
- Database scripts and documentation are pushed to GitHub

---

## Planned Next Milestone

### Milestone 3: Database Connection and Schema Introspection

The next milestone will connect FastAPI to PostgreSQL using SQLAlchemy.

The backend will automatically extract:

- Table names
- Column names
- Data types
- Primary keys
- Foreign keys
- Relationships
- Column descriptions
- Sample categorical values

A new endpoint will be created:

```text
GET /v1/schema
```

The schema must be read directly from PostgreSQL rather than being hardcoded.

---

## Security Notes

The current database account is an administrative development account.

A separate read-only PostgreSQL account will be created before generated SQL is executed.

The final system will use two security layers:

```text
Application-level SQL guardrails
+
PostgreSQL SELECT-only permissions
```

Private API keys and database credentials must never be committed to GitHub.

---

## Author

**Waleed Tariq**

Software Engineering Student  
Ghulam Ishaq Khan Institute of Engineering Sciences and Technology

GitHub:

```text
https://github.com/itswaleedtariq
```