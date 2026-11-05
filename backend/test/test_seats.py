import asyncio

import pytest

from modules.V1.SubscriptionManager.dao import SubscriptionDAO

VENDORS = "/api/v1/vendors"
EMPLOYEES = "/api/v1/employees"
SUBSCRIPTIONS = "/api/v1/subscriptions"


async def make_subscription(client, headers, seat_limit=2, status="active") -> dict:
    vendor = await client.post(VENDORS, json={"name": f"V{seat_limit}{status}"}, headers=headers)
    body = {
        "vendor_id": vendor.json()["data"]["id"],
        "plan_name": "Pro",
        "price": "10.00",
        "billing_cycle": "monthly",
        "seat_limit": seat_limit,
        "renewal_date": "2027-01-01",
        "status": status,
    }
    response = await client.post(SUBSCRIPTIONS, json=body, headers=headers)
    assert response.status_code == 201
    return {**response.json()["data"], "body": body}


async def make_employee(client, headers, number=1) -> int:
    body = {"full_name": f"Person {number}", "email": f"p{number}@acme.io"}
    response = await client.post(EMPLOYEES, json=body, headers=headers)
    assert response.status_code == 201
    return response.json()["data"]["id"]


def seats_url(subscription_id: int) -> str:
    return f"{SUBSCRIPTIONS}/{subscription_id}/seats"


async def assign(client, headers, subscription_id, employee_id):
    return await client.post(
        seats_url(subscription_id), json={"employee_id": employee_id}, headers=headers
    )


async def seat_total(client, headers, subscription_id) -> int:
    response = await client.get(seats_url(subscription_id), headers=headers)
    return response.json()["data"]["total"]


@pytest.fixture
def slow_seat_count(monkeypatch):
    """Hold every request just after counting seats: the moment a race would do its damage.

    Without the row lock, all requests count the same number here and then all insert.
    """
    real_count = SubscriptionDAO.count_seats

    async def count_then_wait(db, subscription_id):
        result = await real_count(db, subscription_id)
        await asyncio.sleep(0.2)
        return result

    monkeypatch.setattr(SubscriptionDAO, "count_seats", count_then_wait)


# ----------------------------------------- Lifecycle -----------------------------------------


async def test_assign_list_and_remove_seat(client, make_company):
    headers = await make_company()
    subscription = await make_subscription(client, headers)
    employee_id = await make_employee(client, headers)

    assigned = await assign(client, headers, subscription["id"], employee_id)
    assert assigned.status_code == 201
    seat = assigned.json()["data"]
    assert seat["employee_id"] == employee_id
    assert seat["employee_email"] == "p1@acme.io"

    listed = await client.get(seats_url(subscription["id"]), headers=headers)
    assert listed.json()["data"]["items"] == [seat]

    url = f"{seats_url(subscription['id'])}/{employee_id}"
    assert (await client.delete(url, headers=headers)).status_code == 200
    assert await seat_total(client, headers, subscription["id"]) == 0
    assert (await client.delete(url, headers=headers)).status_code == 404


async def test_full_plan_rejects_then_accepts_after_a_seat_is_freed(client, make_company):
    headers = await make_company()
    subscription = await make_subscription(client, headers, seat_limit=1)
    first = await make_employee(client, headers, 1)
    second = await make_employee(client, headers, 2)
    await assign(client, headers, subscription["id"], first)

    full = await assign(client, headers, subscription["id"], second)
    assert full.status_code == 409
    assert full.json()["message"] == "No seats available on this plan"

    await client.delete(f"{seats_url(subscription['id'])}/{first}", headers=headers)
    assert (await assign(client, headers, subscription["id"], second)).status_code == 201


async def test_same_employee_cannot_hold_two_seats_on_one_plan(client, make_company):
    headers = await make_company()
    subscription = await make_subscription(client, headers)
    employee_id = await make_employee(client, headers)
    await assign(client, headers, subscription["id"], employee_id)

    response = await assign(client, headers, subscription["id"], employee_id)

    assert response.status_code == 409
    assert response.json()["message"] == "Employee already has this seat"


async def test_cancelled_subscription_rejects_new_seats(client, make_company):
    headers = await make_company()
    subscription = await make_subscription(client, headers, status="cancelled")
    employee_id = await make_employee(client, headers)

    response = await assign(client, headers, subscription["id"], employee_id)

    assert response.status_code == 409
    assert response.json()["message"] == "Subscription is not active"


async def test_employee_with_seat_cannot_be_deleted_until_removed(client, make_company):
    headers = await make_company()
    subscription = await make_subscription(client, headers)
    employee_id = await make_employee(client, headers)
    await assign(client, headers, subscription["id"], employee_id)
    employee_url = f"{EMPLOYEES}/{employee_id}"

    assert (await client.delete(employee_url, headers=headers)).status_code == 409
    await client.delete(f"{seats_url(subscription['id'])}/{employee_id}", headers=headers)
    assert (await client.delete(employee_url, headers=headers)).status_code == 200


@pytest.mark.parametrize(
    "body", [{}, {"employee_id": 0}, {"employee_id": 2147483648}, {"employee_id": 1, "x": 1}]
)
async def test_invalid_seat_input_is_rejected(client, make_company, body):
    headers = await make_company()
    subscription = await make_subscription(client, headers)

    response = await client.post(seats_url(subscription["id"]), json=body, headers=headers)

    assert response.status_code == 422


async def test_missing_records_return_404(client, make_company):
    headers = await make_company()
    subscription = await make_subscription(client, headers)
    employee_id = await make_employee(client, headers)

    assert (await assign(client, headers, 12345, employee_id)).status_code == 404
    assert (await assign(client, headers, subscription["id"], 12345)).status_code == 404
    assert (await client.get(seats_url(12345), headers=headers)).status_code == 404


async def test_endpoints_require_login(client):
    assert (await client.get(seats_url(1))).status_code == 401
    assert (await client.post(seats_url(1), json={"employee_id": 1})).status_code == 401
    assert (await client.delete(f"{seats_url(1)}/1")).status_code == 401


# ---------------------------------------- Isolation ----------------------------------------


async def test_other_company_cannot_touch_seats(client, make_company):
    owner = await make_company()
    intruder = await make_company()
    subscription = await make_subscription(client, owner)
    employee_id = await make_employee(client, owner)
    await assign(client, owner, subscription["id"], employee_id)
    intruder_employee = await make_employee(client, intruder, 2)
    url = f"{seats_url(subscription['id'])}/{employee_id}"

    assert (await client.get(seats_url(subscription["id"]), headers=intruder)).status_code == 404
    assert (
        await assign(client, intruder, subscription["id"], intruder_employee)
    ).status_code == 404
    assert (await client.delete(url, headers=intruder)).status_code == 404
    assert await seat_total(client, owner, subscription["id"]) == 1


async def test_cannot_assign_another_companys_employee(client, make_company):
    owner = await make_company()
    other = await make_company()
    subscription = await make_subscription(client, owner)
    foreign_employee = await make_employee(client, other)

    response = await assign(client, owner, subscription["id"], foreign_employee)

    assert response.status_code == 404
    assert response.json()["message"] == "Employee not found"


# ---------------------------------------- Concurrency ----------------------------------------


async def test_simultaneous_assignments_never_exceed_seat_limit(
    client, make_company, slow_seat_count
):
    headers = await make_company()
    subscription = await make_subscription(client, headers, seat_limit=3)
    employees = [await make_employee(client, headers, n) for n in range(10)]

    responses = await asyncio.gather(
        *(assign(client, headers, subscription["id"], e) for e in employees)
    )

    codes = sorted(r.status_code for r in responses)
    assert codes == [201] * 3 + [409] * 7
    assert await seat_total(client, headers, subscription["id"]) == 3


async def test_lowering_limit_during_assignment_cannot_overfill(
    client, make_company, slow_seat_count
):
    headers = await make_company()
    subscription = await make_subscription(client, headers, seat_limit=2)
    url = f"{SUBSCRIPTIONS}/{subscription['id']}"
    first = await make_employee(client, headers, 1)
    second = await make_employee(client, headers, 2)
    await assign(client, headers, subscription["id"], first)

    await asyncio.gather(
        assign(client, headers, subscription["id"], second),
        client.put(url, json=subscription["body"] | {"seat_limit": 1}, headers=headers),
    )

    limit = (await client.get(url, headers=headers)).json()["data"]["seat_limit"]
    assert await seat_total(client, headers, subscription["id"]) <= limit
