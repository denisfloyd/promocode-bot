from app.config import settings


def test_admin_scrape_requires_token(client):
    response = client.post("/api/v1/admin/scrape")
    assert response.status_code == 403


def test_admin_scrape_wrong_token(client):
    response = client.post("/api/v1/admin/scrape", headers={"X-Admin-Token": "wrong-token"})
    assert response.status_code == 403


def test_admin_scrape_valid_token(client):
    response = client.post(
        "/api/v1/admin/scrape", headers={"X-Admin-Token": settings.admin_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_admin_scrape_telegram(client):
    response = client.post(
        "/api/v1/admin/scrape/telegram", headers={"X-Admin-Token": settings.admin_token}
    )
    assert response.status_code == 200


def test_admin_scrape_status(client):
    response = client.get(
        "/api/v1/admin/scrape/status", headers={"X-Admin-Token": settings.admin_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "telegram_enabled" in data
    assert "channels" in data


def test_admin_scrape_status_requires_token(client):
    response = client.get("/api/v1/admin/scrape/status")
    assert response.status_code == 403
