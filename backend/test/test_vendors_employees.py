"""Vendors and employees follow the same rules, so each test runs against both."""

from dataclasses import dataclass

import pytest
from sqlalchemy import text

from app.database import SessionFactory


@dataclass
class Resource:
    url: str
    valid: dict
    changed: dict
    unique_field: str
    invalid: list[dict]


VENDORS = Resource(
    url="/api/v1/vendors",
    valid={"name": "Slack", "website": "https://slack.com/"},
    changed={"name": "Slack Technologies", "website": None},
    unique_field="name",
    invalid=[
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 256},
        {"name": "a\u0000b"},
        {"name": "Slack", "website": "javascript:alert(1)"},
        {"name": "Slack", "website": "https://a.io/" + "x" * 500},
        {"name": "Slack", "company_id": 999},
        {},
    ],
)
EMPLOYEES = Resource(
    url="/api/v1/employees",
    valid={"full_name": "Asha Rao", "email": "asha@acme.io"},
    changed={"full_name": "Asha R", "email": "a.rao@acme.io"},
    unique_field="email",
    invalid=[
        {"full_name": "", "email": "a@acme.io"},
        {"full_name": "a\u0000b", "email": "a@acme.io"},
        {"full_name": "Asha", "email": "not-an-email"},
        {"full_name": "Asha", "email": "a@acme.io", "company_id": 999},
        {},
    ],
)
RESOURCES = pytest.mark.parametrize("res", [VENDORS, EMPLOYEES], ids=["vendors", "employees"])
BOTH_INVALID = [(VENDORS, b) for b in VENDORS.invalid] + [(EMPLOYEES, b) for b in EMPLOYEES.invalid]


def second(res: Resource, number: int = 2) -> dict:
    """A valid body with different unique values."""
    if res is VENDORS:
        return {"name": f"Vendor {number}"}
    return {"full_name": f"Person {number}", "email": f"person{number}@acme.io"}


async def create(client, res, headers, body=None) -> dict:
    response = await client.post(res.url, json=body or res.valid, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["data"]


# ------------------------------------------ CRUD ------------------------------------------


@RESOURCES
async def test_full_crud_lifecycle(client, make_company, res):
    headers = await make_company()

    created = await create(client, res, headers)
    item_url = f"{res.url}/{created['id']}"
    for key, value in res.valid.items():
        assert created[key] == value
    assert "company_id" not in created

    fetched = await client.get(item_url, headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["data"] == created

    updated = await client.put(item_url, json=res.changed, headers=headers)
    assert updated.status_code == 200
    for key, value in res.changed.items():
        assert updated.json()["data"][key] == value
    assert updated.json()["data"]["updated_at"] > created["updated_at"]
    assert updated.json()["data"]["created_at"] == created["created_at"]

    deleted = await client.delete(item_url, headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["data"] == {"id": created["id"]}
    assert (await client.get(item_url, headers=headers)).status_code == 404


@pytest.mark.parametrize("res, body", BOTH_INVALID)
async def test_invalid_input_is_rejected_on_create_and_update(client, make_company, res, body):
    headers = await make_company()
    existing = await create(client, res, headers)

    created = await client.post(res.url, json=body, headers=headers)
    updated = await client.put(f"{res.url}/{existing['id']}", json=body, headers=headers)

    assert created.status_code == 422
    assert updated.status_code == 422
    listing = await client.get(res.url, headers=headers)
    assert listing.json()["data"]["total"] == 1


@RESOURCES
@pytest.mark.parametrize("bad_id", [0, -1, 2147483648, 99999999999999, "abc"])
async def test_out_of_range_ids_are_rejected_not_crashed(client, make_company, res, bad_id):
    headers = await make_company()

    response = await client.get(f"{res.url}/{bad_id}", headers=headers)

    assert response.status_code == 422


@RESOURCES
async def test_missing_id_returns_404(client, make_company, res):
    headers = await make_company()
    url = f"{res.url}/12345"

    assert (await client.get(url, headers=headers)).status_code == 404
    assert (await client.put(url, json=res.valid, headers=headers)).status_code == 404
    assert (await client.delete(url, headers=headers)).status_code == 404


@RESOURCES
async def test_endpoints_require_login(client, res):
    assert (await client.get(res.url)).status_code == 401
    assert (await client.post(res.url, json=res.valid)).status_code == 401
    assert (await client.get(f"{res.url}/1")).status_code == 401
    assert (await client.put(f"{res.url}/1", json=res.valid)).status_code == 401
    assert (await client.delete(f"{res.url}/1")).status_code == 401


# ---------------------------------------- Uniqueness ----------------------------------------


@RESOURCES
async def test_duplicate_on_create_returns_409(client, make_company, res):
    headers = await make_company()
    await create(client, res, headers)

    response = await client.post(res.url, json=res.valid, headers=headers)

    assert response.status_code == 409
    assert response.json()["status"] == "error"


@RESOURCES
async def test_duplicate_on_update_returns_409_and_changes_nothing(client, make_company, res):
    headers = await make_company()
    first = await create(client, res, headers)
    other = await create(client, res, headers, second(res))

    response = await client.put(f"{res.url}/{other['id']}", json=res.valid, headers=headers)

    assert response.status_code == 409
    unchanged = await client.get(f"{res.url}/{other['id']}", headers=headers)
    assert unchanged.json()["data"][res.unique_field] == other[res.unique_field]
    assert first[res.unique_field] != other[res.unique_field]


@RESOURCES
async def test_update_can_keep_its_own_unique_value(client, make_company, res):
    headers = await make_company()
    item = await create(client, res, headers)

    response = await client.put(f"{res.url}/{item['id']}", json=res.valid, headers=headers)

    assert response.status_code == 200


async def test_employee_email_is_unique_ignoring_case(client, make_company):
    headers = await make_company()
    await create(client, EMPLOYEES, headers)
    body = {"full_name": "Other", "email": "ASHA@ACME.IO"}

    response = await client.post(EMPLOYEES.url, json=body, headers=headers)

    assert response.status_code == 409


@RESOURCES
async def test_two_companies_can_use_the_same_value(client, make_company, res):
    await create(client, res, await make_company())
    await create(client, res, await make_company())


# ---------------------------------------- Isolation ----------------------------------------


@RESOURCES
async def test_other_company_cannot_read_change_or_delete(client, make_company, res):
    owner = await make_company()
    intruder = await make_company()
    item = await create(client, res, owner)
    url = f"{res.url}/{item['id']}"

    assert (await client.get(url, headers=intruder)).status_code == 404
    assert (await client.put(url, json=res.changed, headers=intruder)).status_code == 404
    assert (await client.delete(url, headers=intruder)).status_code == 404

    still_there = await client.get(url, headers=owner)
    assert still_there.json()["data"] == item


@RESOURCES
async def test_list_and_search_only_show_own_company(client, make_company, res):
    owner = await make_company()
    other = await make_company()
    await create(client, res, owner)
    term = res.valid[res.unique_field][:4]

    assert (await client.get(res.url, headers=other)).json()["data"]["total"] == 0
    searched = await client.get(res.url, params={"search": term}, headers=other)
    assert searched.json()["data"]["items"] == []
    found = await client.get(res.url, params={"search": term}, headers=owner)
    assert found.json()["data"]["total"] == 1


# ---------------------------------- Pagination and search ----------------------------------


@RESOURCES
async def test_pagination_returns_stable_pages(client, make_company, res):
    headers = await make_company()
    ids = [(await create(client, res, headers, second(res, n)))["id"] for n in range(5)]

    page = await client.get(res.url, params={"limit": 2, "offset": 2}, headers=headers)

    data = page.json()["data"]
    assert [item["id"] for item in data["items"]] == ids[2:4]
    assert (data["total"], data["limit"], data["offset"]) == (5, 2, 2)


@RESOURCES
@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"offset": 2**40}, {"search": "x" * 256}],
)
async def test_bad_list_params_are_rejected(client, make_company, res, params):
    headers = await make_company()

    assert (await client.get(res.url, params=params, headers=headers)).status_code == 422


@RESOURCES
async def test_search_treats_wildcards_as_plain_text(client, make_company, res):
    headers = await make_company()
    await create(client, res, headers)

    response = await client.get(res.url, params={"search": "%"}, headers=headers)

    assert response.json()["data"]["total"] == 0


# ------------------------------------- Delete protection -------------------------------------


async def _seed_seat(company_id: int, vendor_id: int, employee_id: int) -> None:
    async with SessionFactory() as db:
        subscription_id = await db.scalar(
            text(
                "INSERT INTO subscriptions (company_id, vendor_id, plan_name, price, "
                "billing_cycle, seat_limit, renewal_date) "
                "VALUES (:c, :v, 'Pro', 10, 'monthly', 5, '2027-01-01') RETURNING id"
            ),
            {"c": company_id, "v": vendor_id},
        )
        await db.execute(
            text(
                "INSERT INTO seat_assignments (company_id, subscription_id, employee_id) "
                "VALUES (:c, :s, :e)"
            ),
            {"c": company_id, "s": subscription_id, "e": employee_id},
        )
        await db.commit()


async def test_vendor_and_employee_in_use_cannot_be_deleted(client, make_company):
    headers = await make_company()
    me = await client.get("/api/v1/auth/me", headers=headers)
    vendor = await create(client, VENDORS, headers)
    employee = await create(client, EMPLOYEES, headers)
    await _seed_seat(me.json()["data"]["company_id"], vendor["id"], employee["id"])

    vendor_url = f"{VENDORS.url}/{vendor['id']}"
    employee_url = f"{EMPLOYEES.url}/{employee['id']}"

    assert (await client.delete(vendor_url, headers=headers)).status_code == 409
    assert (await client.delete(employee_url, headers=headers)).status_code == 409
    assert (await client.get(vendor_url, headers=headers)).status_code == 200
    assert (await client.get(employee_url, headers=headers)).status_code == 200
