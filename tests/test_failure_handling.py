from fastapi import status


def test_individual_failure_isolation(client):
    """
    Verify requirement:
    A failure while generating one certificate should not unnecessarily prevent other valid certificates
    in the same job from being generated.
    """
    payload = {
        "title": "Cloud Architect Certificate",
        "course_name": "Cloud Engineering",
        "recipients": [
            {"name": "Valid Recipient One", "email": "valid1@example.com"},
            {"name": "Valid Recipient Two", "email": "valid2@example.com"},
            {"name": "__SIMULATE_FAILURE__BadRecipient", "email": "bad@example.com"},
            {"name": "Valid Recipient Four", "email": "valid4@example.com"},
        ],
    }

    create_res = client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == status.HTTP_201_CREATED
    job_id = create_res.json()["id"]

    # Check job status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == status.HTTP_200_OK
    job = status_res.json()

    assert job["status"] == "COMPLETED_WITH_ERRORS"
    assert job["total_count"] == 4
    assert job["completed_count"] == 3
    assert job["failed_count"] == 1
    assert job["pending_count"] == 0
    assert job["progress_percentage"] == 100.0

    # Retrieve all certificates
    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_res.status_code == status.HTTP_200_OK
    certs = certs_res.json()
    assert len(certs) == 4

    # Verify the failed recipient
    failed_certs = [c for c in certs if c["status"] == "FAILED"]
    assert len(failed_certs) == 1
    failed_cert = failed_certs[0]
    assert failed_cert["recipient_name"] == "__SIMULATE_FAILURE__BadRecipient"
    assert failed_cert["error_reason"] is not None
    assert "Simulated generation failure" in failed_cert["error_reason"]
    assert failed_cert["download_url"] is None

    # Verify the successful recipients
    successful_certs = [c for c in certs if c["status"] == "COMPLETED"]
    assert len(successful_certs) == 3
    for s in successful_certs:
        assert s["download_url"] is not None
        assert s["file_size"] > 0


def test_status_filtering_on_job_certificates(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "Data Analytics",
        "recipients": [
            {"name": "Alice Green", "email": "alice@example.com"},
            {"name": "__SIMULATE_FAILURE__FailedUser", "email": "fail@example.com"},
        ],
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["id"]

    # Filter by FAILED
    failed_res = client.get(f"/api/v1/jobs/{job_id}/certificates?status=FAILED")
    assert failed_res.status_code == status.HTTP_200_OK
    failed_list = failed_res.json()
    assert len(failed_list) == 1
    assert failed_list[0]["recipient_name"] == "__SIMULATE_FAILURE__FailedUser"

    # Filter by COMPLETED
    completed_res = client.get(f"/api/v1/jobs/{job_id}/certificates?status=COMPLETED")
    assert completed_res.status_code == status.HTTP_200_OK
    completed_list = completed_res.json()
    assert len(completed_list) == 1
    assert completed_list[0]["recipient_name"] == "Alice Green"


def test_all_certificates_failed_job_status(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "Testing",
        "recipients": [
            {"name": "__SIMULATE_FAILURE__1", "email": "f1@example.com"},
            {"name": "__SIMULATE_FAILURE__2", "email": "f2@example.com"},
        ],
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["id"]

    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == status.HTTP_200_OK
    job = status_res.json()

    assert job["status"] == "FAILED"
    assert job["completed_count"] == 0
    assert job["failed_count"] == 2
