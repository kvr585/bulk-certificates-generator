from fastapi import status
import pytest
from app.services.storage_service import storage_service, InvalidPathException


def test_get_certificate_metadata(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "FastAPI Testing",
        "recipients": [{"name": "Bruce Banner", "email": "banner@example.com"}],
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["id"]

    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    cert_id = certs_res.json()[0]["id"]

    meta_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert meta_res.status_code == status.HTTP_200_OK
    meta = meta_res.json()
    assert meta["id"] == cert_id
    assert meta["recipient_name"] == "Bruce Banner"
    assert meta["recipient_email"] == "banner@example.com"
    assert meta["status"] == "COMPLETED"
    assert meta["download_url"] == f"/api/v1/certificates/{cert_id}/download"
    assert meta["title"] == payload["title"]
    assert meta["course_name"] == payload["course_name"]


def test_get_nonexistent_certificate(client):
    res = client.get("/api/v1/certificates/nonexistent-cert-id")
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_download_generated_certificate(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "FastAPI Testing",
        "recipients": [{"name": "Tony Stark", "email": "tony@stark.com"}],
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["id"]

    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    cert_id = certs_res.json()[0]["id"]

    download_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_res.status_code == status.HTTP_200_OK
    assert download_res.headers["content-type"] == "application/pdf"
    assert "attachment" in download_res.headers["content-disposition"]
    assert "Certificate_Tony_Stark" in download_res.headers["content-disposition"]
    assert download_res.content.startswith(b"%PDF-")


def test_download_failed_certificate_returns_400(client):
    payload = {
        "title": "Test Title",
        "course_name": "Test Course",
        "recipients": [{"name": "__SIMULATE_FAILURE__User", "email": "fail@example.com"}],
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["id"]

    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    cert_id = certs_res.json()[0]["id"]

    download_res = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "not ready" in download_res.json()["detail"].lower()


def test_download_nonexistent_certificate_returns_404(client):
    download_res = client.get("/api/v1/certificates/nonexistent-cert-id/download")
    assert download_res.status_code == status.HTTP_404_NOT_FOUND


def test_storage_path_traversal_protection():
    with pytest.raises(InvalidPathException):
        storage_service.save_file(
            job_id="../../etc",
            filename="passwd.pdf",
            content=b"test",
        )
