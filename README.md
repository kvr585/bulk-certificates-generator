# Bulk Certificate Generator API

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-23%20passed-brightgreen.svg)]()

A robust, production-grade asynchronous backend service for generating personalized PDF certificates in bulk. Designed with clean separation of concerns, per-recipient failure isolation, real-time progress tracking, and secure file downloads.

---

## 1. Project Overview

Organizations frequently need to issue hundreds or thousands of certificates after training events, bootcamps, or academic courses. Sending one API request per recipient creates network overhead, high latency, and fragile failure handling.

The **Bulk Certificate Generator** solves this by:
1. Allowing the client to submit a single bulk generation request containing multiple recipients.
2. Validating input data strictly using Pydantic.
3. Queueing and processing generation asynchronously in the background.
4. Rendering high-quality vector PDF certificates using ReportLab with custom recipient and event data.
5. Tracking individual status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`) and overall job progress.
6. Isolating failures: if one recipient has corrupt data or generation fails, all valid recipients still receive their certificates.
7. Providing secure download endpoints with path traversal safeguards.

---

## 2. Architecture

The application is structured into decoupled logical layers:

```
                  ┌─────────────────────────────────────────┐
                  │               HTTP Client               │
                  └────────────────────┬────────────────────┘
                                       │
                         JSON Request  │  File Download
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │         FastAPI Routing Layer           │
                  │   (app/api/routes/jobs & certificates)  │
                  └────────────┬────────────────────────────┘
                               │
                Validate Input │ Enqueue Task
                               ▼
    ┌───────────────────────────────────────┐    ┌──────────────────────────┐
    │           Pydantic Schemas            │    │       Job Service        │
    │     (app/schemas/jobs & certs)        │    │ (app/services/job_service)
    └───────────────────────────────────────┘    └─────────────┬────────────┘
                                                               │
                              ┌────────────────────────────────┼──────────────────────────────┐
                              │                                │                              │
                              ▼                                ▼                              ▼
                 ┌─────────────────────────┐      ┌─────────────────────────┐    ┌─────────────────────────┐
                 │     Database Layer      │      │   Certificate Service   │    │     Storage Service     │
                 │  (SQLAlchemy + SQLite)  │      │   (ReportLab Engine)    │    │ (Path Traversal Guard)  │
                 └─────────────────────────┘      └─────────────────────────┘    └─────────────────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full Mermaid sequence diagrams and database ER diagrams.

---

## 3. Technology Stack

- **Language:** Python 3.12+ (tested up to Python 3.14)
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (high performance, automatic OpenAPI documentation)
- **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/) (strict typing, email validation)
- **ORM / Database:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (SQLite for local development, PostgreSQL compatible)
- **PDF Generation:** [ReportLab](https://www.reportlab.com/) (crisp vector rendering, dynamic font-size scaling, custom seals)
- **Testing:** [Pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/) TestClient
- **Containerization:** Docker & Docker Compose

---

## 4. Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & exception handlers
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # Dependency injection (database session)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── certificates.py  # Certificate metadata & download routes
│   │       └── jobs.py          # Job creation, polling, and results routes
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Centralized settings via Pydantic Settings
│   │   └── logging.py           # Structured logging configuration
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy engine, session maker, base
│   │   └── models.py            # Relational models: Job, Certificate, Enums
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py            # Common error & health schemas
│   │   ├── certificates.py      # Recipient input & certificate output schemas
│   │   └── jobs.py              # Job creation & progress schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── certificate_service.py # ReportLab PDF drawing & rendering engine
│   │   ├── job_service.py       # Job lifecycle, transactions & background worker
│   │   └── storage_service.py   # Storage abstraction with traversal protection
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # URL formatting and filename sanitization
├── docs/
│   ├── ARCHITECTURE.md          # Detailed diagrams & design decisions
│   └── REQUIREMENTS_AUDIT.md    # Requirement-by-requirement audit matrix
├── scripts/
│   └── demo.py                  # End-to-end automated live demonstration script
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test database and client fixtures
│   ├── test_certificate_generation.py
│   ├── test_certificate_retrieval.py
│   ├── test_failure_handling.py
│   ├── test_job_status.py
│   ├── test_jobs.py
│   └── test_validation.py
├── Dockerfile                   # Multi-stage production container definition
├── docker-compose.yml           # Local compose deployment specification
├── requirements.txt             # Pinned Python dependencies
├── .env.example                 # Example environment configuration
├── .gitignore                   # Git exclusion rules
└── README.md                    # Project documentation
```

---

## 5. Prerequisites

- Python 3.12 or higher
- Git
- (Optional) Docker & Docker Compose

---

## 6. Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd "Aereo Cloud"
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On macOS / Linux:
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows (PowerShell):
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 7. Environment Configuration

Copy the sample environment file:
```bash
cp .env.example .env
```

Default `.env` configuration:
```env
APP_NAME="Bulk Certificate Generator"
APP_ENV="development"
DEBUG=false
API_V1_STR="/api/v1"
DATABASE_URL="sqlite:///./certificates.db"
STORAGE_LOCAL_DIR="generated_certificates"
MAX_RECIPIENTS_PER_JOB=1000
```

---

## 8. Database Setup

The database tables are initialized automatically upon application startup through the lifespan handler (`init_db()`).

To run on **PostgreSQL**, simply change the `DATABASE_URL` in `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/certificates_db
```

---

## 9. How to Run Locally

Start the development server with Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

The interactive Swagger documentation is immediately accessible at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 10. How to Run with Docker

Build and run using Docker Compose:

```bash
docker compose up --build -d
```

Check logs:
```bash
docker compose logs -f
```

Stop container:
```bash
docker compose down
```

---

## 11. How to Run Tests

Run the complete automated test suite with verbose reporting:

```bash
pytest -v
```

All 23 tests cover:
- Job creation and listing
- Recipient validation (empty list, empty name, malformed email, date parsing)
- PDF generation (vector rendering, long name auto-scaling)
- Real-time progress percentage and status polling
- Fault isolation: one recipient failure does not stop valid siblings
- Metadata retrieval and safe PDF download
- Directory traversal prevention

---

## 12. Automated Live Demonstration

To see the system run an end-to-end batch generation and download a generated PDF directly:

```bash
python scripts/demo.py
```

---

## 13. API Endpoints Table

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/health` | Service health status | `200 OK` |
| `POST` | `/api/v1/jobs` | Create bulk certificate generation job | `201 Created` |
| `GET` | `/api/v1/jobs` | List all generation jobs | `200 OK` |
| `GET` | `/api/v1/jobs/{job_id}` | Get job status, counters, and progress % | `200 OK` |
| `GET` | `/api/v1/jobs/{job_id}/certificates` | List certificates in job (supports `?status=`) | `200 OK` |
| `GET` | `/api/v1/certificates/{certificate_id}` | Get metadata for single certificate | `200 OK` |
| `GET` | `/api/v1/certificates/{certificate_id}/download` | Download generated certificate PDF | `200 OK` |

---

## 14. Usage Examples (curl & JSON)

### Step 1: Submit a Bulk Job

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Certificate of Excellence",
    "course_name": "Cloud Backend Engineering",
    "issuer_name": "Aereo Cloud Academy",
    "issue_date": "2026-10-07",
    "recipients": [
      {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "custom_attributes": {"grade": "A+", "honors": true}
      },
      {
        "name": "John Smith",
        "email": "john@example.com",
        "custom_attributes": {"grade": "A"}
      }
    ]
  }'
```

**Response (HTTP 201 Created):**
```json
{
  "id": "7fa93290-bdf1-4a57-b08e-5b65f048d3c1",
  "title": "Certificate of Excellence",
  "course_name": "Cloud Backend Engineering",
  "issuer_name": "Aereo Cloud Academy",
  "issue_date": "2026-10-07",
  "status": "QUEUED",
  "total_count": 2,
  "completed_count": 0,
  "failed_count": 0,
  "pending_count": 2,
  "error_message": null,
  "created_at": "2026-10-07T13:30:00Z",
  "updated_at": "2026-10-07T13:30:00Z",
  "completed_at": null,
  "progress_percentage": 0.0
}
```

---

### Step 2: Poll Job Status & Progress

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/7fa93290-bdf1-4a57-b08e-5b65f048d3c1"
```

**Response (HTTP 200 OK):**
```json
{
  "id": "7fa93290-bdf1-4a57-b08e-5b65f048d3c1",
  "title": "Certificate of Excellence",
  "course_name": "Cloud Backend Engineering",
  "issuer_name": "Aereo Cloud Academy",
  "issue_date": "2026-10-07",
  "status": "COMPLETED",
  "total_count": 2,
  "completed_count": 2,
  "failed_count": 0,
  "pending_count": 0,
  "error_message": null,
  "created_at": "2026-10-07T13:30:00Z",
  "updated_at": "2026-10-07T13:30:02Z",
  "completed_at": "2026-10-07T13:30:02Z",
  "progress_percentage": 100.0
}
```

---

### Step 3: List Generated Certificates

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/7fa93290-bdf1-4a57-b08e-5b65f048d3c1/certificates"
```

**Response (HTTP 200 OK):**
```json
[
  {
    "id": "c1388b77-cfb5-4a67-933e-e9f0d1991fa9",
    "job_id": "7fa93290-bdf1-4a57-b08e-5b65f048d3c1",
    "recipient_name": "Jane Doe",
    "recipient_email": "jane@example.com",
    "custom_attributes": {"grade": "A+", "honors": true},
    "status": "COMPLETED",
    "file_path": "7fa93290-bdf1-4a57-b08e-5b65f048d3c1/c1388b77-cfb5-4a67-933e-e9f0d1991fa9.pdf",
    "file_size": 3120,
    "download_url": "/api/v1/certificates/c1388b77-cfb5-4a67-933e-e9f0d1991fa9/download",
    "error_reason": null,
    "created_at": "2026-10-07T13:30:00Z",
    "updated_at": "2026-10-07T13:30:01Z",
    "generated_at": "2026-10-07T13:30:01Z"
  }
]
```

---

### Step 4: Download Generated Certificate PDF

```bash
curl -OJ "http://127.0.0.1:8000/api/v1/certificates/c1388b77-cfb5-4a67-933e-e9f0d1991fa9/download"
```

Saves file: `Certificate_Jane_Doe_c1388b77.pdf`.

---

## 15. Certificate Design

The certificate uses a professional vector landscape template designed with ReportLab:
- **Geometry:** A4 landscape (`pagesizes.landscape(A4)`).
- **Styling:** Navy blue outer border, warm gold inner border, gold corner brackets.
- **Official Stamp:** Scalloped vector gold seal with "OFFICIAL VERIFIED" text and decorative ribbon tails.
- **Dynamic Font Scaling:** Automatically detects recipient name lengths (>25 and >35 chars) and scales down typography to avoid visual overflow.
- **Issuer & Signatures:** Prominent organization header, verification ID, issuance date, and program director signature block.

---

## 16. Bulk Processing & Architecture Rationale

### Why FastAPI BackgroundTasks?
For an internship-level backend service, introducing distributed infrastructure like Celery, RabbitMQ, or Redis adds substantial operational complexity without delivering proportional value for batches of hundreds to thousands of records.

FastAPI's built-in `BackgroundTasks` executes operations in a background threadpool immediately after returning the HTTP 201 response.
- **Pros:** Zero extra infrastructure required; instant response to the client; low latency; perfectly suited for local or single-container deployments.
- **Limitations:** Background tasks share process memory. If the application server process crashes or is forcefully terminated, active jobs would require startup recovery logic.

---

## 17. Failure Handling Strategy

1. **Pre-flight Validation (Fast Fail):**
   Malformed emails, empty recipient names, or empty arrays are rejected at the API border with HTTP `422 Unprocessable Content`.
2. **Individual Recipient Isolation:**
   Each recipient in a batch is rendered within its own transaction boundary (`try ... except Exception`).
   - If Recipient 3 encounters an error, its status is marked `FAILED` with diagnostic `error_reason`.
   - Recipients 1, 2, and 4 proceed uninterrupted and succeed (`COMPLETED`).
3. **Job Status Classification:**
   - All succeeded: `COMPLETED`
   - Some succeeded, some failed: `COMPLETED_WITH_ERRORS`
   - All failed: `FAILED`
4. **Information Leakage Prevention:**
   Internal stack traces are logged on the server console with full context, while external clients receive clean JSON error payloads.

---

## 18. File Storage & Security

- **Path Traversal Protection:**
  The `LocalStorageService` strictly verifies that resolved file paths reside within the configured storage directory. Any job ID or filename containing path navigation sequences (`..`, `/`, `\`) is blocked immediately.
- **Non-colliding Identifiers:**
  Files are keyed by random UUIDv4 (`generated_certificates/{job_id}/{certificate_id}.pdf`), eliminating naming collisions and unauthorized file overwrite risks.
- **Content Disposition:**
  File download names are sanitized into safe alphanumeric slugs.

---

## 19. Known Limitations

1. **In-Process Task Queue:** Tasks run inside the web process. A hard process termination (SIGKILL) terminates running background jobs.
2. **Local Disk Storage:** By default, files are persisted to the local filesystem. Multi-instance load balancing requires shared volume or cloud object storage.

---

## 20. Future Improvements

1. **Distributed Task Queue:** Transition `process_job` to Celery with Redis for horizontal multi-worker scaling.
2. **Cloud Storage Backend:** Implement `S3StorageService` under the existing `BaseStorageService` abstraction.
3. **Webhook Notifications:** Allow clients to supply a `webhook_url` to receive a POST notification when a job completes.
4. **Batch ZIP Download:** Add an endpoint (`GET /api/v1/jobs/{id}/download-all`) to stream all completed certificates in a compressed archive.
