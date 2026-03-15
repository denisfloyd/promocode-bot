def test_stats_empty(client):
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_codes"] == 0
    assert data["active_codes"] == 0


def test_stats_with_data(client, sample_codes):
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_codes"] == 3
    assert data["active_codes"] == 2
    assert data["expired_codes"] == 1
    assert data["platforms"]["amazon_br"] == 2
    assert data["platforms"]["mercado_livre"] == 1
