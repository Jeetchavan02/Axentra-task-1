# API examples

A full walkthrough with curl, starting from an empty database and with the API running on port 8000. Run the blocks in order, in one bash or zsh terminal, because later ones use the variables set earlier. The IDs assume an empty database.

The base path for all endpoints is `/api/v1`, and http://localhost:8000/docs has the complete reference.

```bash
BASE=http://localhost:8000/api/v1
```

## Auth

Register a company and its first user:

```bash
curl -s "$BASE/auth/register" -H 'Content-Type: application/json' \
  -d '{"company_name":"Acme","full_name":"Asha Rao","email":"asha@acme.io","password":"correct-horse-battery"}'
```

Log in and keep the token:

```bash
TOKEN=$(curl -s "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"asha@acme.io","password":"correct-horse-battery"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["access_token"])')
```

Check who you are:

```bash
curl -s "$BASE/auth/me" -H "Authorization: Bearer $TOKEN"
```

## Vendors

```bash
curl -s "$BASE/vendors" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Slack","website":"https://slack.com"}'
```

Search and paginate:

```bash
curl -s "$BASE/vendors?search=sla&limit=10&offset=0" -H "Authorization: Bearer $TOKEN"
```

## Subscriptions

`price` is per billing cycle, and `billing_cycle` is `monthly` or `yearly`. `status` is optional, and defaults to `active`.

```bash
curl -s "$BASE/subscriptions" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"vendor_id":1,"plan_name":"Business","price":"120.00","billing_cycle":"yearly","seat_limit":1,"renewal_date":"2030-01-15"}'
```

Filter by status or vendor:

```bash
curl -s "$BASE/subscriptions?status=active&vendor_id=1" -H "Authorization: Bearer $TOKEN"
```

An update replaces all fields:

```bash
curl -s -X PUT "$BASE/subscriptions/1" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"vendor_id":1,"plan_name":"Business","price":"120.00","billing_cycle":"yearly","seat_limit":2,"renewal_date":"2030-01-15"}'
```

## Employees

```bash
curl -s "$BASE/employees" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"full_name":"Ravi Shah","email":"ravi@acme.io"}'
```

## Seats

Assign a seat:

```bash
curl -s "$BASE/subscriptions/1/seats" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"employee_id":1}'
```

List seats:

```bash
curl -s "$BASE/subscriptions/1/seats" -H "Authorization: Bearer $TOKEN"
```

Remove the seat held by employee 1:

```bash
curl -s -X DELETE "$BASE/subscriptions/1/seats/1" -H "Authorization: Bearer $TOKEN"
```

## Reports

Monthly spend counts active plans, with yearly plans at one twelfth of their price:

```bash
curl -s "$BASE/reports/monthly-spend" -H "Authorization: Bearer $TOKEN"
```

Active plans renewing in the next `days` (1 to 365, default 30):

```bash
curl -s "$BASE/reports/upcoming-renewals?days=365" -H "Authorization: Bearer $TOKEN"
```

## Error responses

Errors use the standard format:

```json
{ "code": 409, "message": "No seats available on this plan", "status": "error", "data": null }
```

| Status | Meaning |
|---|---|
| 401 | Missing, invalid or expired token, or wrong login details |
| 404 | The record doesn't exist or belongs to another company |
| 409 | Conflicts with existing data, such as a duplicate, a full plan, or a record still in use |
| 422 | Invalid input; `data.errors` lists each field and problem |
| 503 | `/health` can't reach the database |
