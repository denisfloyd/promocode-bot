def test_list_codes_empty(client):
    response = client.get("/api/v1/codes")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["pagination"]["total"] == 0


def test_list_codes_returns_data(client, sample_codes):
    response = client.get("/api/v1/codes")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert data["pagination"]["total"] == 3


def test_list_codes_filter_by_platform(client, sample_codes):
    response = client.get("/api/v1/codes?platform=amazon_br")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    for code in data["data"]:
        assert code["platform"] == "amazon_br"


def test_list_codes_filter_by_status(client, sample_codes):
    response = client.get("/api/v1/codes?status=active")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2


def test_list_codes_filter_by_min_confidence(client, sample_codes):
    response = client.get("/api/v1/codes?min_confidence=0.7")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["code"] == "AMAZON10"


def test_list_codes_filter_by_category(client, sample_codes):
    response = client.get("/api/v1/codes?category=electronics")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["code"] == "SAVE50"


def test_list_codes_sort_by_confidence_desc(client, sample_codes):
    response = client.get("/api/v1/codes?sort_by=confidence_score&order=desc")
    assert response.status_code == 200
    data = response.json()
    scores = [c["confidence_score"] for c in data["data"]]
    assert scores == sorted(scores, reverse=True)


def test_list_codes_pagination(client, sample_codes):
    response = client.get("/api/v1/codes?page=1&per_page=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 2
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["total_pages"] == 2


def test_list_codes_per_page_max_100(client, sample_codes):
    response = client.get("/api/v1/codes?per_page=200")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["per_page"] == 100


def test_list_codes_filter_by_discount_type(client, sample_codes):
    response = client.get("/api/v1/codes?discount_type=free_shipping")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["code"] == "FRETEGRATIS"


def test_list_codes_sort_ascending(client, sample_codes):
    response = client.get("/api/v1/codes?sort_by=confidence_score&order=asc")
    assert response.status_code == 200
    data = response.json()
    scores = [c["confidence_score"] for c in data["data"]]
    assert scores == sorted(scores)


def test_list_codes_page_beyond_total(client, sample_codes):
    response = client.get("/api/v1/codes?page=999")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["pagination"]["total"] == 3


def test_get_code_by_id(client, sample_code):
    response = client.get(f"/api/v1/codes/{sample_code.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "AMAZON10"
    assert data["id"] == sample_code.id


def test_get_code_not_found(client):
    response = client.get("/api/v1/codes/nonexistent-id")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
