def test_list_platforms(client):
    response = client.get("/api/v1/platforms")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    codes = [p["code"] for p in data["data"]]
    assert "amazon_br" in codes
    assert "mercado_livre" in codes


def test_platforms_include_active_counts(client, sample_codes):
    response = client.get("/api/v1/platforms")
    assert response.status_code == 200
    data = response.json()
    for p in data["data"]:
        if p["code"] == "amazon_br":
            assert p["active_codes"] == 1  # SAVE50 is expired
        elif p["code"] == "mercado_livre":
            assert p["active_codes"] == 1
