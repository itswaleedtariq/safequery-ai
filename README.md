# SafeQuery AI

SafeQuery AI is a secure text-to-SQL platform that converts plain-English questions into PostgreSQL queries, validates them before execution, and returns results with guardrail warnings, hallucination checks, and a confidence score.

The project is designed as a production-oriented AI engineering portfolio project rather than a simple LLM database demo.

## Main Features

- Natural-language to PostgreSQL generation
- Schema-aware prompting with SQLAlchemy
- SQL parsing and validation with SQLGlot
- Blocking of unsafe SQL operations
- Automatic result limits
- `EXPLAIN`-based query checks
- Dedicated read-only PostgreSQL execution user
- SQL-to-question back-translation
- Question and SQL alignment validation
- Schema coverage checks
- Result sanity checks
- Explainable confidence scoring
- JWT signup and login
- Argon2 password hashing
- Protected query endpoint
- React dashboard with light and dark modes

## Queryable Tables

Only these business tables are exposed to the LLM:

- `categories`
- `customers`
- `products`
- `orders`
- `order_items`
- `payments`

Internal tables such as `app_users` are excluded from schema introspection and are not accessible to generated SQL.

## Confidence Score

| Signal | Weight |
|---|---:|
| Safety validation | 20% |
| Question-to-SQL alignment | 30% |
| Result sanity | 20% |
| Multi-query agreement | 15% |
| Schema coverage | 15% |

## Technology Stack

### Backend

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- SQLGlot
- Groq API
- Pydantic
- PyJWT
- Argon2 through `pwdlib`
- Pytest

### Frontend

- React
- TypeScript
- Vite
- React Router
- Lucide React

### Infrastructure

- Docker
- Docker Compose

## Local Setup

### 1. Clone the project

```powershell
git clone https://github.com/itswaleedtariq/safequery-ai.git
cd safequery-ai
```

### 2. Create the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Add your PostgreSQL settings, Groq API key, and JWT secret.

Generate a JWT key:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 4. Start PostgreSQL

```powershell
docker compose up -d
```

### 5. Create application tables

```powershell
python -m backend.app.db.create_app_tables
```

### 6. Start the backend

```powershell
uvicorn backend.app.main:app --reload
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 7. Start the frontend

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

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/v1/auth/signup` | Create an account |
| `POST` | `/v1/auth/login` | Login and receive a JWT |
| `GET` | `/v1/auth/me` | Return the authenticated user |
| `POST` | `/v1/query` | Generate and safely execute SQL |
| `GET` | `/v1/schema` | Return the approved schema |

## Example Questions

```text
How many customers are there?
```

```text
Show completed revenue by month.
```

```text
Which products generated the highest revenue?
```

## Testing

```powershell
python -m pytest backend/tests -v
```

Current verified result:

```text
49 passed
```

Frontend checks:

```powershell
cd frontend
npm run lint
npm run build
```

## Current Limitations

- Query history is not yet stored per user in PostgreSQL.
- Feedback is not yet persisted in the backend.
- JWT tokens are stored in browser `localStorage`.
- Email verification and password reset are not implemented.
- The golden evaluation dataset is still planned.
- The project should not be connected to sensitive production data in its current form.

## Planned Improvements

- Persistent query history
- Persistent feedback
- Golden evaluation dataset
- Automated evaluation report
- HttpOnly cookie authentication
- Refresh tokens
- Login rate limiting

## Author

**Waleed Tariq**  
Software Engineering Undergraduate, GIKI

Focus areas:

- AI Engineering
- Backend Development
- Web Development
- DevOps

GitHub: `https://github.com/itswaleedtariq`