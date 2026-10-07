from fastapi import status


def test_validation_empty_recipient_list(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "Python Backend",
        "recipients": [],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert "errors" in data or "detail" in data


def test_validation_missing_required_fields(client):
    payload = {
        "recipients": [{"name": "Alice"}],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_validation_empty_recipient_name(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "Python Backend",
        "recipients": [{"name": "   ", "email": "test@example.com"}],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_validation_invalid_email(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "Python Backend",
        "recipients": [{"name": "Bob", "email": "not-an-email"}],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_validation_invalid_date(client):
    payload = {
        "title": "Certificate of Completion",
        "course_name": "Python Backend",
        "issue_date": "invalid-date-format",
        "recipients": [{"name": "Bob", "email": "bob@example.com"}],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_validation_exceeding_max_recipients(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_RECIPIENTS_PER_JOB", 3)

    payload = {
        "title": "Certificate of Completion",
        "course_name": "Python Backend",
        "recipients": [{"name": f"User {i}"} for i in range(4)],
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeded" in response.json()["detail"].lower()
