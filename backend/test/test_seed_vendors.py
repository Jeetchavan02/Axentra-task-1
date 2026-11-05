import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seed_vendors.py"
spec = importlib.util.spec_from_file_location("seed_vendors", SCRIPT)
seed_vendors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed_vendors)

URL = "/api/v1/vendors"
OWNER = "owner1@acme.io"


async def vendors(client, headers) -> dict[str, str | None]:
    response = await client.get(URL, params={"limit": 100}, headers=headers)
    return {row["name"]: row["website"] for row in response.json()["data"]["items"]}


async def test_seed_adds_all_vendors_then_nothing_on_second_run(client, make_company):
    headers = await make_company()

    assert await seed_vendors.seed(OWNER) == len(seed_vendors.VENDORS)
    assert await seed_vendors.seed(OWNER) == 0

    assert await vendors(client, headers) == seed_vendors.VENDORS


async def test_seed_keeps_existing_vendor_unchanged(client, make_company):
    headers = await make_company()
    created = await client.post(
        URL, json={"name": "Slack", "website": "https://example.com/"}, headers=headers
    )
    assert created.status_code == 201

    assert await seed_vendors.seed(OWNER) == len(seed_vendors.VENDORS) - 1

    assert (await vendors(client, headers))["Slack"] == "https://example.com/"


async def test_seed_only_touches_that_users_company(client, make_company):
    first = await make_company()
    second = await make_company()

    await seed_vendors.seed("owner2@acme.io")

    assert await vendors(client, first) == {}
    assert len(await vendors(client, second)) == len(seed_vendors.VENDORS)


async def test_seed_finds_email_regardless_of_case(client, make_company):
    await make_company()

    assert await seed_vendors.seed(OWNER.upper()) == len(seed_vendors.VENDORS)


async def test_seed_rejects_unknown_email():
    with pytest.raises(SystemExit, match="No registered user"):
        await seed_vendors.seed("nobody@acme.io")
