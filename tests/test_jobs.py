from fastapi import status


def test_create_bulk_job_success(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "Cloud Architecture & DevOps Masterclass",
        "issuer_name": "Aereo Cloud Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
        ],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["course_name"] == payload["course_name"]
    assert data["total_count"] == 2
    # Because TestClient executes background tasks synchronously:
    assert data["status"] in ["QUEUED", "PROCESSING", "COMPLETED"]


def test_list_jobs(client):
    # Create two jobs
    for i in range(2):
        client.post(
            "/api/v1/jobs",
            json={
                "title": f"Training Batch {i+1}",
                "course_name": "Python Backend",
                "recipients": [{"name": f"User {i+1}", "email": f"user{i+1}@example.com"}],
            },
        )

    response = client.get("/api/v1/jobs")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2


def test_get_nonexistent_job(client):
    response = client.get("/api/v1/jobs/nonexistent-uuid-1234")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()
