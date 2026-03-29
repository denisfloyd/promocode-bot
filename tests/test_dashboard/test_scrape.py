from unittest.mock import patch


def test_scrape_trigger_with_valid_token(client):
    with patch("app.dashboard.routes.settings") as mock_settings:
        mock_settings.admin_token = "test-token"
        with patch("app.services.scheduler._executor") as mock_exec:
            response = client.post(
                "/dashboard/scrape",
                headers={"X-Admin-Token": "test-token"},
            )
            assert response.status_code == 200
            assert "triggered" in response.text.lower()
            mock_exec.submit.assert_called_once()


def test_scrape_trigger_without_token(client):
    response = client.post("/dashboard/scrape")
    assert response.status_code == 200
    assert "invalid" in response.text.lower() or "token" in response.text.lower()
