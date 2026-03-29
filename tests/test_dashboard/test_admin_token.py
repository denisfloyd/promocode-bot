def test_set_admin_token_cookie(client):
    response = client.post(
        "/dashboard/set-token",
        data={"admin_token": "my-secret"},
    )
    assert response.status_code == 200
    assert "saved" in response.text.lower()
    assert "admin_token" in response.cookies
