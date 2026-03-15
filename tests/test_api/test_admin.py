from app.config import settings


def test_admin_scrape_requires_token(client):
    response = client.post("/api/v1/admin/scrape")
    assert response.status_code == 403


def test_admin_scrape_wrong_token(client):
    response = client.post("/api/v1/admin/scrape", headers={"X-Admin-Token": "wrong-token"})
    assert response.status_code == 403


def test_admin_scrape_valid_token(client):
    response = client.post("/api/v1/admin/scrape", headers={"X-Admin-Token": settings.admin_token})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_admin_scrape_platform(client):
    response = client.post("/api/v1/admin/scrape/amazon_br", headers={"X-Admin-Token": settings.admin_token})
    assert response.status_code == 200


def test_admin_scrape_invalid_platform(client):
    response = client.post("/api/v1/admin/scrape/invalid_platform", headers={"X-Admin-Token": settings.admin_token})
    assert response.status_code == 422


def test_admin_scrape_status(client):
    response = client.get("/api/v1/admin/scrape/status", headers={"X-Admin-Token": settings.admin_token})
    assert response.status_code == 200
    data = response.json()
    assert "last_run" in data
    assert "sources" in data


def test_admin_scrape_status_requires_token(client):
    response = client.get("/api/v1/admin/scrape/status")
    assert response.status_code == 403
