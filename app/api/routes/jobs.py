from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import logger
from app.db.models import CertificateStatus
from app.schemas.jobs import JobCreateRequest, JobResponse
from app.schemas.certificates import CertificateResponse
from app.services.job_service import job_service
from app.utils.helpers import build_download_url

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bulk certificate generation job",
    description="Accepts a list of recipients and certificate information, stores the job, and triggers asynchronous certificate generation.",
)
def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if len(request.recipients) > settings.MAX_RECIPIENTS_PER_JOB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exceeded maximum recipient limit of {settings.MAX_RECIPIENTS_PER_JOB} per job",
        )

    job = job_service.create_bulk_job(db, request)

    # Enqueue background task
    background_tasks.add_task(job_service.process_job, job.id)
    logger.info("Queued background generation for Job %s", job.id)

    return job


@router.get(
    "",
    response_model=List[JobResponse],
    summary="List all certificate generation jobs",
    description="Retrieve a paginated list of all created jobs.",
)
def list_jobs(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    db: Session = Depends(get_db),
):
    jobs, _ = job_service.list_jobs(db, skip=skip, limit=limit)
    return jobs


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job status and progress",
    description="Return real-time job status, total recipients, completed count, failed count, and progress percentage.",
)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )
    return job


@router.get(
    "/{job_id}/certificates",
    response_model=List[CertificateResponse],
    summary="Get certificates for a job",
    description="Retrieve individual certificate records and generation outcomes for a specific job, with optional status filter.",
)
def get_job_certificates(
    job_id: str,
    status_filter: Optional[CertificateStatus] = Query(None, alias="status", description="Filter by status (PENDING, PROCESSING, COMPLETED, FAILED)"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Limit records returned"),
    db: Session = Depends(get_db),
):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )

    certificates, _ = job_service.get_job_certificates(
        db, job_id=job_id, status=status_filter, skip=skip, limit=limit
    )

    # Attach download_url for completed certificates
    response_items = []
    for cert in certificates:
        item = CertificateResponse.model_validate(cert)
        if cert.status == CertificateStatus.COMPLETED:
            item.download_url = build_download_url(cert.id)
        response_items.append(item)

    return response_items
