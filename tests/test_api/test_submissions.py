def test_submit_code(client):
    response = client.post(
        "/api/v1/codes",
        json={
            "code": "MEUCODIGO",
            "platform": "amazon_br",
            "description": "10% off em tudo",
            "discount_type": "percentage",
            "discount_value": 10.0,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Code submitted"
    assert "id" in data


def test_submit_code_appears_in_list(client):
    client.post(
        "/api/v1/codes",
        json={
            "code": "NOVOCODIGO",
            "platform": "mercado_livre",
            "description": "R$50 de desconto",
            "discount_type": "fixed_amount",
            "discount_value": 50.0,
            "min_purchase": 200.0,
        },
    )
    response = client.get("/api/v1/codes?platform=mercado_livre")
    assert response.status_code == 200
    codes = [c["code"] for c in response.json()["data"]]
    assert "NOVOCODIGO" in codes


def test_submit_duplicate_code(client):
    payload = {
        "code": "DUPLICADO",
        "platform": "amazon_br",
        "description": "Test",
        "discount_type": "percentage",
        "discount_value": 5.0,
    }
    client.post("/api/v1/codes", json=payload)
    response = client.post("/api/v1/codes", json=payload)
    assert response.status_code == 409
    assert "duplicate" in response.json()["error"]["code"]


def test_submit_code_with_category(client):
    response = client.post(
        "/api/v1/codes",
        json={
            "code": "ELETRO20",
            "platform": "amazon_br",
            "description": "20% off em eletrônicos",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "category": "electronics",
        },
    )
    assert response.status_code == 201

    # Verify it's filterable by category
    response = client.get("/api/v1/codes?category=electronics")
    assert len(response.json()["data"]) == 1
