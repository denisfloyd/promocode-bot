def test_vote_worked_returns_updated_row(client, sample_code):
    response = client.post(f"/dashboard/codes/{sample_code.id}/vote?worked=true")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "1W" in response.text  # 1 worked vote
    assert "AMAZON10" in response.text


def test_vote_failed_returns_updated_row(client, sample_code):
    response = client.post(f"/dashboard/codes/{sample_code.id}/vote?worked=false")
    assert response.status_code == 200
    assert "1F" in response.text  # 1 failed vote


def test_vote_nonexistent_code(client):
    response = client.post("/dashboard/codes/nonexistent/vote?worked=true")
    assert response.status_code == 200
    assert "not found" in response.text.lower()
