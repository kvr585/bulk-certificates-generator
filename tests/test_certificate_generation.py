from datetime import date
from app.services.certificate_service import certificate_service, CertificateGenerationError
import pytest


def test_generate_pdf_valid():
    pdf_bytes = certificate_service.generate_pdf(
        certificate_id="test-cert-uuid-1234",
        recipient_name="Eleanor Vance",
        title="Certificate of Achievement",
        course_name="Distributed Cloud Systems",
        issuer_name="Aereo Cloud Academy",
        issue_date=date(2026, 10, 7),
        custom_attributes={"grade": "Distinction", "honors": True},
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic number header
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_pdf_long_name_scaling():
    long_name = "Dr. Alexander Bartholomew Montgomery-Cunningham III"
    pdf_bytes = certificate_service.generate_pdf(
        certificate_id="test-long-name-123",
        recipient_name=long_name,
        title="Certificate of Completion",
        course_name="Machine Learning Engineering",
        issuer_name="Aereo Cloud Academy",
        issue_date=date(2026, 10, 7),
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_generate_pdf_simulated_failure():
    with pytest.raises(CertificateGenerationError):
        certificate_service.generate_pdf(
            certificate_id="fail-test-id",
            recipient_name="__SIMULATE_FAILURE__BadRecipient",
            title="Certificate of Completion",
            course_name="Testing",
            issuer_name="Academy",
            issue_date=date.today(),
        )
