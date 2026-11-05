# Architecture

## Request flow

```text
HTTP request
    ↓
routers.py      Defines the endpoint, its typed inputs, and the login requirement
    ↓
controller.py   Calls the service and builds the standard response
    ↓
services.py     Business rules and transaction control
    ↓
dao.py          Database queries
    ↓
models.py       Table definitions
```

`schemas.py` defines the request and response shapes, and `api_docs.py` holds the endpoint descriptions. Simple reads may go from the controller straight to the DAO.

## Response format

Every response, including errors, has the same shape. `code` always matches the HTTP status.

```json
{ "code": 200, "message": "Success", "status": "success", "data": {} }
```

## Data model

```text
companies ─┬─ users
           ├─ vendors ───── subscriptions ─┐
           └─ employees ───────────────────┴─ seat_assignments
```

## Key decisions

**Company isolation.** `company_id` comes only from the login token, and every query filters by it. Sending `company_id` in a request body returns 422. Another company's record returns 404, so its existence isn't revealed. Composite foreign keys also stop the database from linking records across companies.

**Seat limit under concurrency.** Assigning a seat locks the subscription row (`SELECT ... FOR UPDATE`), counts the seats, then inserts and commits. Simultaneous requests take turns, so two can't claim the last seat. Lowering `seat_limit` takes the same lock.

**One session per request.** A service can run several steps in one transaction, so they all succeed or all roll back.

**Database constraints are the final check.** Uniqueness and delete protection are enforced by the database, and the service turns violations into a 409. Deletes use `RESTRICT`, so nothing is removed by a cascade.

**Money.** Prices use `Numeric(10, 2)` and are sent in JSON as strings, because floats can't store amounts like 0.10 exactly.

**Errors.** Tracebacks stay in the server log, and validation errors don't echo the rejected input.

**Login.** A wrong password and an unknown email get identical responses. A deleted user's token stops working immediately, because each request loads the user from the database.

**Migrations.** The schema is managed by Alembic. The test suite builds its database through the same migrations, so they get tested too.

## Based on the reference template

This project follows the layout and layers of the reference template, with its own domain and these changes:

| Reference template | This project |
|---|---|
| Parses the raw `Request` | Typed Pydantic inputs, so validation and docs are automatic |
| Errors return HTTP 200 and include tracebacks | Real status codes, and tracebacks only in logs |
| Update and delete don't check the tenant | Every query is scoped to the company |
| Each database helper opens its own session | One session per request |
| Redis, Celery, ARQ, Prometheus, second database | Left out, as this project doesn't need them |

## Frontend

The React app in `frontend/` is a thin client for testing the API, and all rules stay in the backend. `src/api.js` adds the token and turns error responses into readable messages. `ResourcePage` provides list, search, create, edit and delete from a field config, and each screen supplies its own config.

The token is kept in `sessionStorage`, so closing the tab logs the user out. A 401 on any request returns to the login screen.

## Known limits

- **Frontend tests.** The frontend has no automated tests. It was checked by hand in a browser.
- **Dropdown size.** The vendor and employee dropdowns load the first 100 records.
- **No refresh tokens or logout.** Tokens last 60 minutes and can't be revoked individually.
- **No roles.** Every user in a company can do everything.
- **One currency.** Monthly spend is a simple total.
- **Overdue renewals.** The renewals report excludes past dates, and renewal dates don't advance automatically.
- **Cancelled subscriptions.** They reject new seats, but existing seats stay until removed, and those seats block deletion.
- **Rounding.** The monthly total can differ from the rounded per-vendor lines by a cent.
- **Dates.** Renewal windows use the UTC date.
- **Conflict message.** If a vendor is deleted at the moment a subscription is created for it, the request is safely rejected, but the message says the plan is a duplicate.
