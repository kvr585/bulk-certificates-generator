#!/usr/bin/env python3
"""
Interactive / Automated Demo Script for Bulk Certificate Generator.
Demonstrates:
1. Health check verification
2. Submitting a bulk job with valid & edge-case recipients
3. Polling progress & job status
4. Retrieving certificate list (completed vs failed)
5. Downloading the generated certificate PDF
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db

def run_demo():
    print("=" * 70)
    print("BULK CERTIFICATE GENERATOR — LIVE SYSTEM DEMONSTRATION")
    print("=" * 70)

    # 1. Initialize DB
    print("\n[Step 1] Initializing database tables...")
    init_db()
    print("  -> Database tables initialized.")

    client = TestClient(app)

    # 2. Health check
    print("\n[Step 2] Checking API health endpoint (GET /health)...")
    res = client.get("/health")
    print(f"  -> HTTP {res.status_code}: {res.json()}")

    # 3. Submit bulk job
    print("\n[Step 3] Submitting bulk generation job (POST /api/v1/jobs)...")
    job_payload = {
        "title": "Certificate of Excellence in Cloud Engineering",
        "course_name": "Modern Backend Architecture with FastAPI",
        "issuer_name": "Aereo Cloud Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Ananya Sharma", "email": "ananya@example.com", "custom_attributes": {"grade": "Distinction", "honors": True}},
            {"name": "Marcus Aurelius Vance", "email": "marcus@example.com", "custom_attributes": {"grade": "A+"}},
            {"name": "__SIMULATE_FAILURE__CorruptRecord", "email": "corrupt@example.com"},
            {"name": "Sophia Zhang", "email": "sophia@example.com", "custom_attributes": {"grade": "Distinction"}},
        ],
    }

    create_res = client.post("/api/v1/jobs", json=job_payload)
    if create_res.status_code != 201:
        print(f"  -> Error creating job: {create_res.text}")
        sys.exit(1)

    job_data = create_res.json()
    job_id = job_data["id"]
    print(f"  -> Job created successfully! Job ID: {job_id}")
    print(f"  -> Total recipients submitted: {job_data['total_count']}")

    # 4. Check status & progress
    print("\n[Step 4] Checking job status and progress (GET /api/v1/jobs/{job_id})...")
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    status_data = status_res.json()
    print(f"  -> Status: {status_data['status']}")
    print(f"  -> Total: {status_data['total_count']}")
    print(f"  -> Completed: {status_data['completed_count']}")
    print(f"  -> Failed: {status_data['failed_count']}")
    print(f"  -> Pending: {status_data['pending_count']}")
    print(f"  -> Progress: {status_data['progress_percentage']}%")

    # 5. List certificates
    print("\n[Step 5] Listing individual certificate records (GET /api/v1/jobs/{job_id}/certificates)...")
    certs_res = client.get(f"/api/v1/jobs/{job_id}/certificates")
    certs = certs_res.json()
    for idx, cert in enumerate(certs, 1):
        status_flag = "[OK]" if cert["status"] == "COMPLETED" else "[FAILED]"
        print(f"  {idx}. {status_flag} {cert['recipient_name']} ({cert['status']})")
        if cert["error_reason"]:
            print(f"      Reason: {cert['error_reason']}")
        if cert["download_url"]:
            print(f"      Download URL: {cert['download_url']} (Size: {cert['file_size']} bytes)")

    # 6. Download a certificate
    completed_certs = [c for c in certs if c["status"] == "COMPLETED"]
    if completed_certs:
        target_cert = completed_certs[0]
        cert_id = target_cert["id"]
        print(f"\n[Step 6] Downloading certificate for '{target_cert['recipient_name']}'...")
        download_res = client.get(f"/api/v1/certificates/{cert_id}/download")
        print(f"  -> HTTP {download_res.status_code}")
        print(f"  -> Content-Type: {download_res.headers.get('content-type')}")
        print(f"  -> Content-Disposition: {download_res.headers.get('content-disposition')}")
        print(f"  -> Received {len(download_res.content)} bytes of PDF data.")

        demo_pdf_path = Path("demo_output_certificate.pdf")
        demo_pdf_path.write_bytes(download_res.content)
        print(f"  -> Saved sample certificate to: {demo_pdf_path.resolve()}")

    print("\n" + "=" * 70)
    print("DEMO RUN COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
