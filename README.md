SafeQuery AI

A secure natural-language-to-SQL analytics platform that converts plain-English business questions into validated PostgreSQL queries, executes them through a read-only database role, detects likely hallucinations, and returns results with an explainable confidence score.

SafeQuery AI is a portfolio-grade AI engineering project. It goes beyond basic SQL generation by combining schema-aware prompting, AST-based SQL guardrails, query-plan validation, read-only execution, hallucination checks, confidence scoring, JWT authentication, and a React dashboard.

Problem

Text-to-SQL can make relational data accessible to non-technical users, but generated SQL creates important risks:

Destructive or unauthorized operations

Incorrect joins, filters, and aggregations

Queries that answer a different question

Excessive scans or expensive execution plans

Hallucinated tables and columns

Exposure of authentication or other internal tables

Results presented with unjustified confidence

SafeQuery AI uses several independent controls to validate a generated query before execution and to evaluate its result before displaying it.

Features

Natural-language querying

Users can ask questions such as:

How many customers are there?

Show completed revenue by month.

Which products generated the highest revenue?

The backend generates PostgreSQL, validates it, runs it safely, and returns structured results.

Schema-aware generation

SQLAlchemy introspection provides the model with approved schema information:

Tables and columns

Data types

Primary keys

Foreign-key relationships

Indexes

Computed columns

Low-cardinality sample values

Business definitions

A strict allowlist exposes only the six analytics tables. Internal application tables such as app_users are excluded.

SQL guardrails

SQL is parsed with SQLGlot and checked before execution. The safety layer:

Allows read-only queries

Blocks DML writes

Blocks DDL operations

Rejects multiple statements

Rejects SQL comments

Blocks dangerous functions

Rejects unknown tables and columns

Rejects ambiguous unqualified columns

Restricts subquery depth

Applies and caps row limits

Uses EXPLAIN for cost and scan validation

Enforces query timeout controls

Read-only execution

Generated SQL is executed with a dedicated PostgreSQL reader role. That role has SELECT access only to the approved business tables and no access to authentication data.

Hallucination detection

The validation pipeline checks generated SQL using:

SQL-to-question back-translation

Question/SQL alignment scoring

Expected schema coverage

Aggregate and business-rule checks

Result sanity checks

Independent-query agreement where available

Specific issue and warning codes

Confidence scoring

The composite confidence score uses:

Signal

Weight

Safety validation

20%

Question-to-SQL alignment

30%

Result sanity

20%

Independent-query agreement

15%

Schema coverage

15%

High hallucination risk or result disagreement can cap the final score.

JWT authentication

The application includes:

Backend signup and login

Argon2 password hashing

Signed JWT access tokens

Protected /v1/auth/me

Protected query execution

Frontend session restoration

Automatic logout for expired or invalid tokens

Passwords are never stored in plain text.

React interface

The frontend includes:

Home and About pages

Signup and Login pages

Protected query workspace

Generated SQL display

Result table

Confidence breakdown

Guardrail and validation warnings

Sample questions

Feedback controls

Browser-persisted theme

Light and dark modes

Responsive layout

Custom SafeQuery AI branding

Architecture

flowchart TD
    U[User] --> F[React Frontend]
    F --> API[FastAPI API]

    API --> AUTH[JWT Authentication]
    AUTH --> APPDB[(Application Tables)]

    API --> WF[Query Workflow]
    WF --> SCHEMA[Schema Introspection and Allowlist]
    SCHEMA --> PROMPT[Schema-Aware Prompt Builder]
    PROMPT --> LLM[Groq LLM]
    LLM --> SQL[Structured SQL Output]

    SQL --> GUARD[SQLGlot Guardrails]
    GUARD --> PLAN[EXPLAIN Validation]
    PLAN --> DB[(Read-Only PostgreSQL Role)]

    DB --> SANITY[Result Sanity Checks]
    SQL --> BACK[SQL Back-Translation]
    BACK --> ALIGN[Alignment Validation]
    SCHEMA --> COVER[Schema Coverage]

    SANITY --> HALL[Hallucination Detector]
    ALIGN --> HALL
    COVER --> HALL
    HALL --> CONF[Confidence Scorer]
    CONF --> API

Technology Stack

Backend

Python 3.11+

FastAPI

Pydantic

SQLAlchemy 2.x

PostgreSQL 17

SQLGlot

Groq API

PyJWT

pwdlib with Argon2

Pytest

Frontend

React

TypeScript

Vite

React Router

Lucide React

CSS light and dark themes

Development infrastructure

Docker

Docker Compose

PostgreSQL initialization scripts

Separate application and read-only database access

Database

The analytics dataset contains six queryable tables:

Table

Purpose

categories

Product categories

customers

Customer records

products

Product catalog and pricing

orders

Order-level records

order_items

Product-level order details

payments

Payment records

Internal tables such as app_users are never exposed to the LLM.

Revenue definition

Revenue is calculated as:

SUM(order_items.line_total)

for orders with a status of completed or shipped.

Project Structure

safequery-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── data/
│   │   ├── db/
│   │   ├── guardrails/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── validators/
│   │   └── main.py
│   └── tests/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   ├── utils/
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── main.tsx
│   │   └── types.ts
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md

API

Authentication

Method

Endpoint

Purpose

Auth

POST

/v1/auth/signup

Create an account and issue a JWT

No

POST

/v1/auth/login

Validate credentials and issue a JWT

No

GET

/v1/auth/me

Return the authenticated user

Bearer JWT

Query system

Method

Endpoint

Purpose

Auth

POST

/v1/query

Generate, validate, execute, and score SQL

Bearer JWT

GET

/v1/schema

Return the approved analytics schema

Current API configuration

Local OpenAPI documentation:

http://127.0.0.1:8000/docs

Local Setup

Prerequisites

Python 3.11 or later

Node.js and npm

Docker Desktop

Git

Groq API key

The project has been developed on Windows PowerShell with Python 3.13.1.

1. Clone the repository

git clone https://github.com/itswaleedtariq/safequery-ai.git
cd safequery-ai

2. Create the virtual environment

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

3. Configure backend environment variables

Copy-Item .env.example .env

Example configuration:

DATABASE_URL=postgresql+psycopg://safequery_admin:your_password@localhost:5433/safequery_db
READONLY_DATABASE_URL=postgresql+psycopg://safequery_reader:your_reader_password@localhost:5433/safequery_db
DATABASE_SCHEMA=public

GROQ_API_KEY=replace_with_your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_MINUTES=60

Generate a secure JWT secret:

python -c "import secrets; print(secrets.token_urlsafe(48))"

Never commit .env.

4. Start PostgreSQL

docker compose up -d
docker compose ps

The current local configuration exposes PostgreSQL on host port 5433.

5. Create application tables

python -m backend.app.db.create_app_tables

Expected output:

SafeQuery application tables created successfully.

6. Start the backend

uvicorn backend.app.main:app --reload

Backend:

http://127.0.0.1:8000

7. Configure and start the frontend

Open another terminal:

cd frontend
Copy-Item .env.example .env
npm install
npm run dev

Frontend .env:

VITE_API_BASE_URL=http://127.0.0.1:8000

Frontend:

http://localhost:5173

Authentication Flow

Signup request

{
  "name": "Waleed Tariq",
  "email": "waleed@example.com",
  "password": "SafeQuery123!"
}

The backend normalizes the email, checks uniqueness, hashes the password with Argon2, stores the user, and returns a signed access token.

Login request

{
  "email": "waleed@example.com",
  "password": "SafeQuery123!"
}

Protected request

Authorization: Bearer <access-token>

The frontend restores an existing session by calling /v1/auth/me.

Example Query

{
  "question": "How many customers are there?"
}

A successful response can include:

Generated SQL

SQL explanation

Guardrail decision

Result rows and columns

Row count

Execution time

Query plan

Hallucination status

Alignment score

Schema coverage

Result sanity findings

Confidence score and breakdown

Warnings

The exact contract is defined by the backend Pydantic schemas.

Demo Questions

How many customers are there?

How many orders were placed in each status?

Which products generated the highest completed revenue?

Show completed revenue by month.

Which customers placed the most orders?

Show revenue by product category.

Ambiguous questions can trigger a clarification request rather than forcing the model to guess.

Testing

Run all backend tests:

python -m pytest backend/tests -v

Current verified result:

49 passed

The suite covers confidence scoring, hallucination detection, prompt construction, schema introspection, SQL generation schemas, SQL guardrails, query execution, read-only role use, workflow behavior, clarification handling, and low-confidence result gating.

Compile the backend:

python -m compileall backend

Run frontend checks:

cd frontend
npm run lint
npm run build

Security Model

SafeQuery AI uses defense in depth:

Schema isolation: only six business tables are exposed.

Structured generation: model output is validated with Pydantic.

AST parsing: SQLGlot parses SQL structurally.

Guardrails: unsafe operations and invalid references are rejected.

Plan validation: EXPLAIN checks query cost and scans.

Read-only role: database permissions block writes and private tables.

Result validation: alignment, coverage, business rules, and sanity are checked.

Confidence gating: questionable results can be hidden or accompanied by warnings.

Authentication: Argon2 hashes and JWT bearer tokens protect user access.

Current Limitations

Query history and feedback are not yet persisted per user in PostgreSQL.

JWT access tokens are stored in browser localStorage.

Refresh-token rotation is not implemented.

Email verification and password reset are not implemented.

The golden evaluation dataset is not yet complete.

Automated evaluation reports are not yet included.

The sample database is intended for demonstration and testing.

LLM-generated SQL can still be wrong; confidence and warnings must be reviewed.

The system should not be connected to sensitive production data in its current form.

Planned Enhancements

PostgreSQL-backed user query history

Persistent correct/incorrect feedback

User-scoped history authorization

Golden natural-language-to-SQL dataset

Execution-result comparison against verified SQL

Automated accuracy and hallucination reports

HttpOnly cookie-based sessions

Refresh-token rotation

Login rate limiting

Email verification and password reset

Expanded audit logging

Stronger ambiguity detection

Additional multi-query validation

Design Decisions

Why PostgreSQL?

PostgreSQL provides realistic SQL behavior, query plans, generated columns, relationships, permissions, and role-based security.

Why SQLGlot?

SQLGlot enables dialect-aware parsing and structural inspection of statements, tables, columns, functions, limits, comments, and subqueries.

Why a read-only database role?

Application validation is not a sufficient security boundary. Database permissions prevent writes even if an application check fails.

Why a strict table allowlist?

A denylist could expose future tables accidentally. With an allowlist, new authentication, history, session, or feedback tables remain private by default.

Why SQL back-translation?

A syntactically valid query can still answer the wrong question. Back-translation creates a natural-language interpretation that can be compared with the original request.

Why an explainable confidence score?

A single unexplained number is difficult to trust. SafeQuery AI exposes the safety, alignment, sanity, agreement, and schema-coverage signals behind the final score.

Portfolio Skills Demonstrated

AI application architecture

Structured LLM outputs

Prompt engineering

Text-to-SQL generation

SQL parsing and validation

PostgreSQL security

Role-based access control

Hallucination detection

Confidence calibration

FastAPI service design

React and TypeScript

JWT authentication

SQLAlchemy

Docker-based development

Automated testing

Security-oriented AI engineering

The project focuses not only on generating SQL, but on determining whether the SQL is safe, relevant, and trustworthy enough to execute and display.

Author

Waleed TariqSoftware Engineering Undergraduate, GIKI

Focus areas:

AI Engineering

Backend Development

Web Development

DevOps

Database Systems

GitHub: https://github.com/itswaleedtariq

License

This project is intended for educational, portfolio, and demonstration purposes.

Add a LICENSE file before external distribution. The MIT License is a suitable choice when reuse with attribution is permitted.

Acknowledgment

SafeQuery AI was developed from a production-oriented text-to-SQL project blueprint emphasizing guardrails, hallucination detection, confidence scoring, a query interface, and an evaluation workflow. The implementation extends that concept with PostgreSQL role isolation, strict schema filtering, JWT authentication, and a React dashboard.