def test_full_dashboard_flow(client, sample_codes):
    # 1. Load main page
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "PromoCode Dashboard" in response.text
    assert "htmx.org" in response.text
    assert "pico" in response.text

    # 2. Load stats
    response = client.get("/dashboard/stats")
    assert response.status_code == 200
    assert "Active Codes" in response.text

    # 3. Load codes
    response = client.get("/dashboard/codes")
    assert response.status_code == 200
    assert "AMAZON10" in response.text

    # 4. Filter by platform
    response = client.get("/dashboard/codes?platform=mercado_livre")
    assert "FRETEGRATIS" in response.text
    assert "AMAZON10" not in response.text

    # 5. Vote on a code
    code_id = sample_codes[0].id
    response = client.post(f"/dashboard/codes/{code_id}/vote?worked=true")
    assert response.status_code == 200
    assert "1W" in response.text


def test_dashboard_no_codes(client):
    response = client.get("/dashboard/codes")
    assert response.status_code == 200
    assert "No codes found" in response.text


def test_existing_api_still_works(client, sample_codes):
    """Ensure the JSON API is unaffected by dashboard changes."""
    response = client.get("/api/v1/codes")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 3
