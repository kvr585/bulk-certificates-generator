from fastapi import status


def test_job_status_and_progress_tracking(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "Full Stack Backend with FastAPI",
        "recipients": [
            {"name": "Alice Smith", "email": "alice@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"},
            {"name": "Charlie Brown", "email": "charlie@example.com"},
        ],
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == status.HTTP_201_CREATED
    job_id = create_res.json()["id"]

    # Poll status endpoint
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == status.HTTP_200_OK
    job_data = status_res.json()

    assert job_data["id"] == job_id
    assert job_data["status"] == "COMPLETED"
    assert job_data["total_count"] == 3
    assert job_data["completed_count"] == 3
    assert job_data["failed_count"] == 0
    assert job_data["pending_count"] == 0
    assert job_data["progress_percentage"] == 100.0
    assert job_data["completed_at"] is not None


def test_get_job_certificates_listing(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "FastAPI Certification",
        "recipients": [
            {"name": "Diana Prince", "email": "diana@example.com"},
            {"name": "Bruce Wayne", "email": "bruce@example.com"},
        ],
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["id"]

    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_res.status_code == status.HTTP_200_OK
    certs = certs_res.json()
    assert len(certs) == 2
    assert all(c["status"] == "COMPLETED" for c in certs)
    assert all(c["download_url"] is not None for c in certs)
