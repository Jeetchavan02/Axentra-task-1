async def test_health_reports_database_ok(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["data"] == {"status": "ok", "database": "ok"}


async def test_unknown_route_uses_standard_error_format(client):
    response = await client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json()["status"] == "error"
    assert response.json()["code"] == 404
