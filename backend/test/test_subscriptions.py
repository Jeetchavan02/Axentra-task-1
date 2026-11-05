import pytest
from sqlalchemy import text

from app.database import SessionFactory

URL = "/api/v1/subscriptions"
VENDORS = "/api/v1/vendors"


async def make_vendor(client, headers, name="Slack") -> int:
    response = await client.post(VENDORS, json={"name": name}, headers=headers)
    assert response.status_code == 201
    return response.json()["data"]["id"]


def body(vendor_id: int, /, **overrides) -> dict:
    return {
        "vendor_id": vendor_id,
        "plan_name": "Business",
        "price": "99.50",
        "billing_cycle": "monthly",
        "seat_limit": 5,
        "renewal_date": "2027-01-15",
    } | overrides


async def make_subscription(client, headers, vendor_id, **overrides) -> dict:
    response = await client.post(URL, json=body(vendor_id, **overrides), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def seed_seats(client, headers, subscription_id: int, count: int) -> None:
    me = await client.get("/api/v1/auth/me", headers=headers)
    company_id = me.json()["data"]["company_id"]
    async with SessionFactory() as db:
        for number in range(count):
            employee_id = await db.scalar(
                text(
                    "INSERT INTO employees (company_id, full_name, email) "
                    "VALUES (:c, 'Seat Holder', :e) RETURNING id"
                ),
                {"c": company_id, "e": f"seat{subscription_id}-{number}@acme.io"},
            )
            await db.execute(
                text(
                    "INSERT INTO seat_assignments (company_id, subscription_id, employee_id) "
                    "VALUES (:c, :s, :e)"
                ),
                {"c": company_id, "s": subscription_id, "e": employee_id},
            )
        await db.commit()


async def test_full_crud_lifecycle(client, make_company):
    headers = await make_company()
    vendor_id = await make_vendor(client, headers)

    created = await make_subscription(client, headers, vendor_id)
    url = f"{URL}/{created['id']}"
    assert created["price"] == "99.50"
    assert created["status"] == "active"
    assert "company_id" not in created

    assert (await client.get(url, headers=headers)).json()["data"] == created

    changed = body(vendor_id, plan_name="Enterprise", price="0", status="cancelled")
    updated = await client.put(url, json=changed, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["data"]["plan_name"] == "Enterprise"
    assert updated.json()["data"]["status"] == "cancelled"
    assert updated.json()["data"]["updated_at"] > created["updated_at"]

    assert (await client.delete(url, headers=headers)).status_code == 200
    assert (await client.get(url, headers=headers)).status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        {"price": "-1"},
        {"price": "1.999"},
        {"price": "123456789.00"},
        {"price": "NaN"},
        {"price": "Infinity"},
        {"seat_limit": 0},
        {"seat_limit": 2147483648},
        {"billing_cycle": "weekly"},
        {"status": "paused"},
        {"renewal_date": "not-a-date"},
        {"plan_name": "  "},
        {"plan_name": "a\u0000b"},
        {"vendor_id": 2147483648},
        {"company_id": 999},
    ],
)
async def test_invalid_input_is_rejected_on_create_and_update(client, make_company, overrides):
    headers = await make_company()
    vendor_id = await make_vendor(client, headers)
    existing = await make_subscription(client, headers, vendor_id)
    bad = body(vendor_id, plan_name="Other") | overrides

    assert (await client.post(URL, json=bad, headers=headers)).status_code == 422
    assert (
        await client.put(f"{URL}/{existing['id']}", json=bad, headers=headers)
    ).status_code == 422


async def test_duplicate_plan_returns_409_on_create_and_update(client, make_company):
    headers = await make_company()
    vendor_id = await make_vendor(client, headers)
    await make_subscription(client, headers, vendor_id)
    other = await make_subscription(client, headers, vendor_id, plan_name="Pro")

    assert (await client.post(URL, json=body(vendor_id), headers=headers)).status_code == 409
    response = await client.put(f"{URL}/{other['id']}", json=body(vendor_id), headers=headers)
    assert response.status_code == 409


async def test_unknown_vendor_returns_404(client, make_company):
    headers = await make_company()

    response = await client.post(URL, json=body(12345), headers=headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Vendor not found"


# ---------------------------------------- Isolation ----------------------------------------


async def test_cannot_use_another_companys_vendor(client, make_company):
    owner = await make_company()
    intruder = await make_company()
    foreign_vendor = await make_vendor(client, owner)
    own_vendor = await make_vendor(client, intruder, "Figma")
    own = await make_subscription(client, intruder, own_vendor)

    created = await client.post(URL, json=body(foreign_vendor), headers=intruder)
    updated = await client.put(f"{URL}/{own['id']}", json=body(foreign_vendor), headers=intruder)

    assert created.status_code == 404
    assert updated.status_code == 404


async def test_other_company_cannot_read_change_or_delete(client, make_company):
    owner = await make_company()
    intruder = await make_company()
    vendor_id = await make_vendor(client, owner)
    item = await make_subscription(client, owner, vendor_id)
    intruder_vendor = await make_vendor(client, intruder)
    url = f"{URL}/{item['id']}"

    assert (await client.get(url, headers=intruder)).status_code == 404
    assert (await client.put(url, json=body(intruder_vendor), headers=intruder)).status_code == 404
    assert (await client.delete(url, headers=intruder)).status_code == 404
    assert (await client.get(url, headers=owner)).json()["data"] == item


async def test_list_only_shows_own_company(client, make_company):
    owner = await make_company()
    other = await make_company()
    vendor_id = await make_vendor(client, owner)
    await make_subscription(client, owner, vendor_id)

    assert (await client.get(URL, headers=other)).json()["data"]["total"] == 0
    filtered = await client.get(URL, params={"vendor_id": vendor_id}, headers=other)
    assert filtered.json()["data"]["total"] == 0


async def test_endpoints_require_login(client):
    assert (await client.get(URL)).status_code == 401
    assert (await client.post(URL, json=body(1))).status_code == 401
    assert (await client.get(f"{URL}/1")).status_code == 401
    assert (await client.put(f"{URL}/1", json=body(1))).status_code == 401
    assert (await client.delete(f"{URL}/1")).status_code == 401


# ------------------------------------- Filters and pagination -------------------------------------


async def test_filters_search_and_pagination(client, make_company):
    headers = await make_company()
    slack = await make_vendor(client, headers, "Slack")
    figma = await make_vendor(client, headers, "Figma")
    first = await make_subscription(client, headers, slack, plan_name="Pro Monthly")
    second = await make_subscription(client, headers, figma, plan_name="Team", status="cancelled")
    third = await make_subscription(client, headers, figma, plan_name="Pro Yearly")

    async def ids(**params) -> list[int]:
        response = await client.get(URL, params=params, headers=headers)
        return [item["id"] for item in response.json()["data"]["items"]]

    assert await ids(status="cancelled") == [second["id"]]
    assert await ids(vendor_id=figma) == [second["id"], third["id"]]
    assert await ids(search="pro") == [first["id"], third["id"]]
    assert await ids(search="pro", vendor_id=figma, status="active") == [third["id"]]
    assert await ids(search="%") == []
    assert await ids(limit=1, offset=1) == [second["id"]]


@pytest.mark.parametrize(
    "params", [{"status": "paused"}, {"vendor_id": 0}, {"vendor_id": 2147483648}, {"limit": 101}]
)
async def test_bad_list_params_are_rejected(client, make_company, params):
    headers = await make_company()

    assert (await client.get(URL, params=params, headers=headers)).status_code == 422


# ---------------------------------------- Seat rules ----------------------------------------


async def test_subscription_with_seats_cannot_be_deleted(client, make_company):
    headers = await make_company()
    vendor_id = await make_vendor(client, headers)
    item = await make_subscription(client, headers, vendor_id)
    await seed_seats(client, headers, item["id"], 1)

    response = await client.delete(f"{URL}/{item['id']}", headers=headers)

    assert response.status_code == 409
    assert (await client.get(f"{URL}/{item['id']}", headers=headers)).status_code == 200


async def test_vendor_with_subscription_cannot_be_deleted(client, make_company):
    headers = await make_company()
    vendor_id = await make_vendor(client, headers)
    await make_subscription(client, headers, vendor_id)

    response = await client.delete(f"{VENDORS}/{vendor_id}", headers=headers)

    assert response.status_code == 409


@pytest.mark.parametrize("new_limit, expected", [(1, 409), (2, 200), (3, 200)])
async def test_seat_limit_cannot_drop_below_seats_in_use(client, make_company, new_limit, expected):
    headers = await make_company()
    vendor_id = await make_vendor(client, headers)
    item = await make_subscription(client, headers, vendor_id)
    await seed_seats(client, headers, item["id"], 2)

    response = await client.put(
        f"{URL}/{item['id']}", json=body(vendor_id, seat_limit=new_limit), headers=headers
    )

    assert response.status_code == expected


@pytest.mark.parametrize("method", ["post", "put"])
async def test_vendor_deleted_during_request_returns_404(client, make_company, monkeypatch, method):
    headers = await make_company()
    vendor_id = await make_vendor(client, headers)
    subscription = await make_subscription(client, headers, vendor_id)

    # The vendor check passes, as if the vendor were deleted just after it ran.
    async def vendor_still_there(*_):
        return object()

    monkeypatch.setattr("modules.V1.VendorManager.dao.VendorDAO.get", vendor_still_there)
    gone = body(999999, plan_name="Other")
    if method == "post":
        response = await client.post(URL, json=gone, headers=headers)
    else:
        response = await client.put(f"{URL}/{subscription['id']}", json=gone, headers=headers)

    assert response.status_code == 404
    assert response.json()["message"] == "Vendor not found"
