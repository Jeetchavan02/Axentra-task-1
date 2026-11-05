from datetime import UTC, datetime, timedelta

import pytest

VENDORS = "/api/v1/vendors"
SUBSCRIPTIONS = "/api/v1/subscriptions"
RENEWALS = "/api/v1/reports/upcoming-renewals"
SPEND = "/api/v1/reports/monthly-spend"


async def make_vendor(client, headers, name="Slack") -> int:
    response = await client.post(VENDORS, json={"name": name}, headers=headers)
    return response.json()["data"]["id"]


async def make_subscription(client, headers, vendor_id, plan="Pro", days=10, **overrides) -> int:
    renewal = datetime.now(UTC).date() + timedelta(days=days)
    body = {
        "vendor_id": vendor_id,
        "plan_name": plan,
        "price": "10.00",
        "billing_cycle": "monthly",
        "seat_limit": 1,
        "renewal_date": renewal.isoformat(),
    } | overrides
    response = await client.post(SUBSCRIPTIONS, json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


async def test_renewals_respect_window_status_and_order(client, make_company):
    headers = await make_company()
    vendor = await make_vendor(client, headers)
    later = await make_subscription(client, headers, vendor, "Later", days=30)
    today = await make_subscription(client, headers, vendor, "Today", days=0)
    await make_subscription(client, headers, vendor, "Past", days=-1)
    await make_subscription(client, headers, vendor, "Beyond", days=31)
    await make_subscription(client, headers, vendor, "Cancelled", days=5, status="cancelled")

    response = await client.get(RENEWALS, headers=headers)

    data = response.json()["data"]
    assert [item["subscription_id"] for item in data["items"]] == [today, later]
    assert data["total"] == 2
    assert data["items"][0]["days_until_renewal"] == 0
    assert data["items"][1]["days_until_renewal"] == 30
    assert data["items"][0]["vendor_name"] == "Slack"


async def test_renewals_days_parameter_widens_window(client, make_company):
    headers = await make_company()
    vendor = await make_vendor(client, headers)
    await make_subscription(client, headers, vendor, days=60)

    assert (await client.get(RENEWALS, headers=headers)).json()["data"]["total"] == 0
    wide = await client.get(RENEWALS, params={"days": 60}, headers=headers)
    assert wide.json()["data"]["total"] == 1


@pytest.mark.parametrize("params", [{"days": 0}, {"days": 366}, {"limit": 0}])
async def test_renewals_bad_params_are_rejected(client, make_company, params):
    headers = await make_company()

    assert (await client.get(RENEWALS, params=params, headers=headers)).status_code == 422


async def test_monthly_spend_normalizes_yearly_and_skips_cancelled(client, make_company):
    headers = await make_company()
    slack = await make_vendor(client, headers, "Slack")
    figma = await make_vendor(client, headers, "Figma")
    await make_subscription(client, headers, slack, "Monthly", price="5.00")
    await make_subscription(
        client, headers, slack, "Yearly", price="120.00", billing_cycle="yearly"
    )
    await make_subscription(
        client, headers, figma, "Yearly", price="100.00", billing_cycle="yearly"
    )
    await make_subscription(client, headers, figma, "Old", price="999.00", status="cancelled")

    data = (await client.get(SPEND, headers=headers)).json()["data"]

    assert data["total_monthly_spend"] == "23.33"
    assert data["active_subscriptions"] == 3
    assert [(v["vendor_name"], v["monthly_spend"]) for v in data["by_vendor"]] == [
        ("Figma", "8.33"),
        ("Slack", "15.00"),
    ]


async def test_monthly_spend_is_zero_without_subscriptions(client, make_company):
    headers = await make_company()

    data = (await client.get(SPEND, headers=headers)).json()["data"]

    assert data == {"total_monthly_spend": "0.00", "active_subscriptions": 0, "by_vendor": []}


async def test_reports_only_include_own_company(client, make_company):
    owner = await make_company()
    other = await make_company()
    vendor = await make_vendor(client, owner)
    await make_subscription(client, owner, vendor)

    assert (await client.get(RENEWALS, headers=other)).json()["data"]["total"] == 0
    spend = (await client.get(SPEND, headers=other)).json()["data"]
    assert spend["total_monthly_spend"] == "0.00"
    assert spend["by_vendor"] == []


async def test_reports_require_login(client):
    assert (await client.get(RENEWALS)).status_code == 401
    assert (await client.get(SPEND)).status_code == 401
