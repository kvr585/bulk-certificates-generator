from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.db.database import SessionLocal
from app.db.models import Job, Certificate, JobStatus, CertificateStatus
from app.schemas.jobs import JobCreateRequest
from app.services.certificate_service import certificate_service
from app.services.storage_service import storage_service


class JobService:
    """Manages the lifecycle, database persistence, and background execution of bulk generation jobs."""

    @classmethod
    def create_bulk_job(cls, db: Session, request: JobCreateRequest) -> Job:
        """
        Creates a Job record and pre-creates individual Certificate records in PENDING status.
        Ensures atomic persistence before queueing background tasks.
        """
        total = len(request.recipients)

        job = Job(
            title=request.title,
            course_name=request.course_name,
            issuer_name=request.issuer_name,
            issue_date=request.issue_date,
            status=JobStatus.QUEUED,
            total_count=total,
            completed_count=0,
            failed_count=0,
            pending_count=total,
        )
        db.add(job)
        db.flush()  # Generate job.id

        for recipient in request.recipients:
            cert = Certificate(
                job_id=job.id,
                recipient_name=recipient.name,
                recipient_email=str(recipient.email) if recipient.email else None,
                custom_attributes=recipient.custom_attributes,
                status=CertificateStatus.PENDING,
            )
            db.add(cert)

        db.commit()
        db.refresh(job)
        logger.info("Created Job %s with %d recipients", job.id, total)
        return job

    @classmethod
    def process_job(cls, job_id: str) -> None:
        """
        Background worker function that executes bulk generation.
        Uses an isolated database session and provides fault isolation per recipient.
        """
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error("Background task: Job %s not found", job_id)
                return

            job.status = JobStatus.PROCESSING
            db.commit()
            logger.info("Started processing Job %s", job_id)

            # Retrieve all certificates for this job
            certificates = (
                db.query(Certificate)
                .filter(Certificate.job_id == job_id, Certificate.status == CertificateStatus.PENDING)
                .all()
            )

            for cert in certificates:
                cls._process_single_certificate(db, job, cert)

            # Refresh counts from DB to guarantee absolute accuracy
            completed_count = (
                db.query(Certificate)
                .filter(Certificate.job_id == job_id, Certificate.status == CertificateStatus.COMPLETED)
                .count()
            )
            failed_count = (
                db.query(Certificate)
                .filter(Certificate.job_id == job_id, Certificate.status == CertificateStatus.FAILED)
                .count()
            )
            pending_count = (
                db.query(Certificate)
                .filter(Certificate.job_id == job_id, Certificate.status.in_([CertificateStatus.PENDING, CertificateStatus.PROCESSING]))
                .count()
            )

            job.completed_count = completed_count
            job.failed_count = failed_count
            job.pending_count = pending_count
            job.completed_at = datetime.now(timezone.utc)

            # Determine final job status
            if failed_count == 0:
                job.status = JobStatus.COMPLETED
            elif completed_count == 0:
                job.status = JobStatus.FAILED
            else:
                job.status = JobStatus.COMPLETED_WITH_ERRORS

            db.commit()
            logger.info(
                "Finished processing Job %s: %s (Completed: %d, Failed: %d)",
                job_id,
                job.status.value,
                completed_count,
                failed_count,
            )

        except Exception as e:
            logger.error("Fatal failure while processing job %s: %s", job_id, str(e), exc_info=True)
            try:
                db.rollback()
                failed_job = db.query(Job).filter(Job.id == job_id).first()
                if failed_job:
                    failed_job.status = JobStatus.FAILED
                    failed_job.error_message = f"Fatal processing error: {str(e)}"
                    failed_job.completed_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception as rollback_err:
                logger.error("Failed to record fatal job error: %s", str(rollback_err))
        finally:
            db.close()

    @classmethod
    def _process_single_certificate(cls, db: Session, job: Job, cert: Certificate) -> None:
        """
        Process generation for an individual certificate.
        Any exception is trapped and recorded, never interrupting sibling certificates.
        """
        try:
            cert.status = CertificateStatus.PROCESSING
            db.commit()

            # Generate PDF in-memory
            pdf_bytes = certificate_service.generate_pdf(
                certificate_id=cert.id,
                recipient_name=cert.recipient_name,
                title=job.title,
                course_name=job.course_name,
                issuer_name=job.issuer_name,
                issue_date=job.issue_date,
                custom_attributes=cert.custom_attributes,
            )

            # Persist securely via storage abstraction
            filename = f"{cert.id}.pdf"
            stored_path = storage_service.save_file(
                job_id=job.id,
                filename=filename,
                content=pdf_bytes,
            )

            cert.file_path = stored_path
            cert.file_size = len(pdf_bytes)
            cert.status = CertificateStatus.COMPLETED
            cert.error_reason = None
            cert.generated_at = datetime.now(timezone.utc)

            job.completed_count += 1
            if job.pending_count > 0:
                job.pending_count -= 1

            db.commit()
            logger.debug("Successfully generated certificate %s for %s", cert.id, cert.recipient_name)

        except Exception as e:
            logger.warning(
                "Failed generating certificate %s for recipient %s: %s",
                cert.id,
                cert.recipient_name,
                str(e),
            )
            db.rollback()

            cert.status = CertificateStatus.FAILED
            cert.error_reason = str(e)
            job.failed_count += 1
            if job.pending_count > 0:
                job.pending_count -= 1

            db.commit()

    @classmethod
    def get_job(cls, db: Session, job_id: str) -> Optional[Job]:
        """Fetch job by ID."""
        return db.query(Job).filter(Job.id == job_id).first()

    @classmethod
    def list_jobs(cls, db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[Job], int]:
        """Fetch paginated list of jobs."""
        total = db.query(Job).count()
        jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
        return jobs, total

    @classmethod
    def get_job_certificates(
        cls,
        db: Session,
        job_id: str,
        status: Optional[CertificateStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Certificate], int]:
        """Fetch paginated certificates for a job, optionally filtered by status."""
        query = db.query(Certificate).filter(Certificate.job_id == job_id)
        if status:
            query = query.filter(Certificate.status == status)
        total = query.count()
        certs = query.order_by(Certificate.created_at.asc()).offset(skip).limit(limit).all()
        return certs, total

    @classmethod
    def get_certificate(cls, db: Session, certificate_id: str) -> Optional[Certificate]:
        """Fetch single certificate by ID."""
        return db.query(Certificate).filter(Certificate.id == certificate_id).first()


job_service = JobService()
