def test_dashboard_page_returns_html(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "PromoCode Dashboard" in response.text


def test_stats_partial_returns_html(client):
    response = client.get("/dashboard/stats")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_stats_partial_shows_counts(client, sample_codes):
    response = client.get("/dashboard/stats")
    assert response.status_code == 200
    # sample_codes has 2 active (AMAZON10 + FRETEGRATIS) and 1 expired (SAVE50)
    assert ">2<" in response.text  # active count
    assert ">1<" in response.text  # expired count
