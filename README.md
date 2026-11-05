# Subscription Tracker

A FastAPI backend that helps a company track its software subscriptions: which vendors it pays, who holds a seat on each plan, what renews soon, and what it spends each month.

Each company's data is isolated. A subscription can never go over its seat limit, even when requests arrive at the same time.

## Features

- **Auth:** register a company, log in, and use JWT access tokens
- **Vendors, employees, subscriptions:** full CRUD with pagination and search
- **Seats:** assign and remove seats, with the limit enforced under concurrent requests
- **Reports:** upcoming renewals and monthly spend

## Stack

FastAPI, async SQLAlchemy 2, PostgreSQL 17 (Docker), Alembic, PyJWT, bcrypt, pytest, ruff, uv.

## Setup

You need [uv](https://docs.astral.sh/uv/) and Docker. uv installs the Python version the project uses.

**1. Create your config.** From the repository root:

```bash
cd backend
cp .env.example .env
```

In `.env`, set your own `DB_PASSWORD` and set `JWT_SECRET` to the output of:

```bash
openssl rand -hex 32
```

The app won't start until `JWT_SECRET` has at least 32 characters.

**2. Start the database and create the tables:**

```bash
docker compose up -d --wait
uv sync
uv run alembic upgrade head
```

**3. Run the API:**

```bash
uv run uvicorn app.main:app --app-dir src --reload
```

Open http://localhost:8000/docs for interactive API docs. To call protected endpoints there: register, log in, then paste the `access_token` into **Authorize**.

## Tests

The tests create and use a separate `subscription_tracker_test` database, so they never touch your development data. The database container must be running.

```bash
uv run pytest
```

```bash
uv run ruff check .
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md): layers, decisions, and known limits
- [API examples](docs/API.md): a full walkthrough with curl

## Repository layout

```text
backend/
├── src/
│   ├── app/                  # Shared setup: settings, database, security, errors, responses
│   └── modules/V1/           # One folder per feature
│       ├── AuthManager/
│       ├── VendorManager/
│       ├── EmployeeManager/
│       ├── SubscriptionManager/
│       ├── SeatManager/
│       └── ReportManager/
├── alembic/                  # Database migrations
├── test/
└── docker-compose.yml
docs/
```
