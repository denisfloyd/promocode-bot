def test_codes_partial_returns_html(client, sample_codes):
    response = client.get("/dashboard/codes")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_codes_partial_shows_codes(client, sample_codes):
    response = client.get("/dashboard/codes")
    assert "AMAZON10" in response.text
    assert "FRETEGRATIS" in response.text
    assert "SAVE50" in response.text


def test_codes_partial_filters_by_platform(client, sample_codes):
    response = client.get("/dashboard/codes?platform=amazon_br")
    assert "AMAZON10" in response.text
    assert "FRETEGRATIS" not in response.text


def test_codes_partial_filters_by_min_confidence(client, sample_codes):
    # sample_codes: AMAZON10=0.8, FRETEGRATIS=0.6, SAVE50=0.3
    response = client.get("/dashboard/codes?min_confidence=0.5")
    assert "AMAZON10" in response.text
    assert "FRETEGRATIS" in response.text
    assert "SAVE50" not in response.text


def test_codes_partial_sorts_by_confidence_desc(client, sample_codes):
    response = client.get("/dashboard/codes?sort_by=confidence_score")
    text = response.text
    # AMAZON10 (0.8) should appear before FRETEGRATIS (0.6)
    assert text.index("AMAZON10") < text.index("FRETEGRATIS")


def test_codes_partial_paginates(client, sample_codes):
    response = client.get("/dashboard/codes?per_page=2&page=1")
    assert response.status_code == 200
    # Should have pagination controls
    assert "page=" in response.text


def test_codes_partial_empty(client):
    response = client.get("/dashboard/codes")
    assert response.status_code == 200
    assert "No codes found" in response.text
