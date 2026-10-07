# Bulk Certificate Generator — Architecture & System Design

## 1. System Overview

The **Bulk Certificate Generator** is an asynchronous backend service engineered to process batch certificate generation requests reliably. The architecture separates client request handling from compute-heavy PDF generation while isolating failures at the individual recipient level.

```mermaid
graph TD
    Client["Client / API Consumer"] -->|POST /api/v1/jobs| API["FastAPI Route Layer (app/api/routes)"]
    API -->|Validate Schema| Pydantic["Pydantic Schemas (app/schemas)"]
    API -->|Create Records| JobService["Job Service (app/services/job_service.py)"]
    JobService -->|Persist Job & Certs| DB[(Relational DB: SQLite / Postgres)]
    API -->|Enqueue Task| BG["FastAPI BackgroundTasks"]
    API -->|HTTP 201 Created| Client

    BG -->|Execute Async| Worker["Job Worker (process_job)"]
    Worker -->|Fetch Pending Certs| DB
    loop For Each Recipient
        Worker -->|Render Vector PDF| CertService["Certificate Service (ReportLab)"]
        CertService -->|Raw PDF Bytes| Worker
        Worker -->|Persist File| StorageService["Storage Service (LocalStorage)"]
        StorageService -->|Save .pdf| Disk["Secure Disk Storage"]
        Worker -->|Update Status (COMPLETED / FAILED)| DB
    end
    Worker -->|Update Final Job Status| DB

    Client -->|GET /api/v1/jobs/{id}| API
    Client -->|GET /api/v1/certificates/{id}/download| API
    API -->|Stream PDF File| Client
```

---

## 2. Request & Execution Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Client
    participant API as FastAPI Router
    participant DB as Database (SQLAlchemy)
    participant BG as Background Task
    participant CS as Certificate Service
    participant FS as Storage Service

    User->>API: POST /api/v1/jobs (Title, Course, Recipients[])
    API->>API: Validate input (names, emails, dates, limits)
    API->>DB: INSERT Job (QUEUED) & Certificates (PENDING)
    API->>BG: Enqueue job_service.process_job(job_id)
    API-->>User: 201 Created (Job ID, initial counters)

    Note over BG: Asynchronous execution starts
    BG->>DB: UPDATE Job status = PROCESSING
    loop Each Recipient
        BG->>DB: UPDATE Certificate status = PROCESSING
        alt Generation Succeeded
            BG->>CS: generate_pdf(recipient_name, course, etc.)
            CS-->>BG: PDF binary stream
            BG->>FS: save_file(job_id, cert_id.pdf, bytes)
            FS-->>BG: File path
            BG->>DB: UPDATE Certificate (COMPLETED, file_path) & increment completed_count
        else Generation Failed / Corrupt
            BG->>DB: UPDATE Certificate (FAILED, error_reason) & increment failed_count
        end
    end
    BG->>DB: UPDATE Job status (COMPLETED / COMPLETED_WITH_ERRORS / FAILED)

    User->>API: GET /api/v1/jobs/{job_id}
    API->>DB: Query job & counters
    API-->>User: 200 OK (Job status, progress_percentage, counts)

    User->>API: GET /api/v1/certificates/{id}/download
    API->>DB: Query certificate & verify COMPLETED
    API->>FS: get_file_path(job_id, cert_id.pdf)
    API-->>User: 200 OK (application/pdf stream)
```

---

## 3. Database Entity-Relationship Diagram

```mermaid
erDiagram
    JOB ||--o{ CERTIFICATE : "contains"
    JOB {
        string id PK "UUID4"
        string title "Certificate title"
        string course_name "Course/Event name"
        string issuer_name "Issuing organization"
        date issue_date "Issuance date"
        string status "QUEUED, PROCESSING, COMPLETED, COMPLETED_WITH_ERRORS, FAILED"
        int total_count "Total recipients requested"
        int completed_count "Successfully generated count"
        int failed_count "Failed generation count"
        int pending_count "Remaining count"
        text error_message "Fatal job error details"
        datetime created_at "Creation timestamp UTC"
        datetime updated_at "Update timestamp UTC"
        datetime completed_at "Completion timestamp UTC"
    }

    CERTIFICATE {
        string id PK "UUID4"
        string job_id FK "References jobs.id (CASCADE DELETE)"
        string recipient_name "Recipient full name"
        string recipient_email "Optional email address"
        json custom_attributes "Optional metadata (grades, honors)"
        string status "PENDING, PROCESSING, COMPLETED, FAILED"
        string file_path "Relative storage path"
        int file_size "File size in bytes"
        text error_reason "Failure diagnostics"
        datetime created_at "Creation timestamp UTC"
        datetime updated_at "Update timestamp UTC"
        datetime generated_at "Generation timestamp UTC"
    }
```

---

## 4. Failure Handling & Isolation Flow

```mermaid
flowchart TD
    Start["Receive Batch of N Recipients"] --> PreValidation{"Pre-flight Validation"}
    PreValidation -->|Malformed JSON / Empty List| Reject["422 Unprocessable Content (Fast Fail)"]
    PreValidation -->|Valid Batch| Persist["Persist Job (QUEUED) & N Certificates (PENDING)"]
    Persist --> Worker["Worker Processes Batch in Background"]

    Worker --> Loop["Process Recipient i"]
    Loop --> TryGen["Try: Generate PDF & Save to Disk"]
    TryGen -->|Success| MarkSuccess["Certificate -> COMPLETED<br/>job.completed_count += 1"]
    TryGen -->|Exception| CatchErr["Catch Exception<br/>Certificate -> FAILED<br/>Store error_reason<br/>job.failed_count += 1"]

    MarkSuccess --> CheckMore{"More recipients?"}
    CatchErr --> CheckMore

    CheckMore -->|Yes| Loop
    CheckMore -->|No| CheckCounts{"Inspect Job Counts"}

    CheckCounts -->|failed == 0| SetCompleted["Job Status -> COMPLETED"]
    CheckCounts -->|completed > 0 and failed > 0| SetPartial["Job Status -> COMPLETED_WITH_ERRORS"]
    CheckCounts -->|completed == 0 and failed > 0| SetFailed["Job Status -> FAILED"]
```

---

## 5. Architectural & Design Decisions

### 5.1 Asynchronous Background Processing
- **Decision:** Utilize FastAPI's native `BackgroundTasks` executing in a managed threadpool.
- **Rationale:** The assignment specifies keeping the infrastructure lean without over-engineering (no Redis, Celery, or RabbitMQ). FastAPI's `BackgroundTasks` allows immediate HTTP 201 response times while processing PDF rendering in the background.
- **Trade-off / Limitations:** Background tasks share the web process memory space. If the server process is forcefully terminated mid-flight, unfinished in-memory tasks would need resumption logic. For multi-node horizontal scaling, a distributed message broker (Celery + Redis/RabbitMQ) would be the next step.

### 5.2 Storage Service Abstraction (`BaseStorageService`)
- **Decision:** Encapsulate disk I/O behind an abstract base class `BaseStorageService` with a concrete `LocalStorageService`.
- **Rationale:** Prevents route handlers from directly manipulating filesystems. Guarantees strict directory traversal prevention (`..` and separator checks) while providing a pluggable interface for future Amazon S3 or Google Cloud Storage backends.

### 5.3 Deterministic Progress Tracking
- **Decision:** Store explicit counters (`total_count`, `completed_count`, `failed_count`, `pending_count`) on the `Job` model and dynamically compute `progress_percentage`.
- **Rationale:** Polling clients can query progress with a single fast `O(1)` index-assisted primary key lookup on the `jobs` table without performing costly `COUNT(*)` aggregates across thousands of certificates on every poll.
