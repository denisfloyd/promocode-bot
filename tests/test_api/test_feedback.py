def test_submit_feedback_worked(client, sample_code):
    response = client.post(
        f"/api/v1/codes/{sample_code.id}/feedback",
        json={"worked": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["votes_worked"] == 1
    assert data["votes_failed"] == 0
    assert data["message"] == "Feedback submitted"
    assert "confidence_score" in data


def test_submit_feedback_did_not_work(client, sample_code):
    response = client.post(
        f"/api/v1/codes/{sample_code.id}/feedback",
        json={"worked": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["votes_worked"] == 0
    assert data["votes_failed"] == 1


def test_submit_feedback_code_not_found(client):
    response = client.post(
        "/api/v1/codes/nonexistent/feedback",
        json={"worked": True},
    )
    assert response.status_code == 404


def test_submit_feedback_duplicate_vote_same_day(client, sample_code, db_session):
    client.post(
        f"/api/v1/codes/{sample_code.id}/feedback",
        json={"worked": True},
    )
    response = client.post(
        f"/api/v1/codes/{sample_code.id}/feedback",
        json={"worked": True},
    )
    assert response.status_code == 429
    data = response.json()
    assert "already voted" in data["error"]["message"].lower()
