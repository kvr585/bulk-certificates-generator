from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.logging import logger
from app.db.models import CertificateStatus
from app.schemas.certificates import CertificateMetadataResponse
from app.services.job_service import job_service
from app.services.storage_service import storage_service
from app.utils.helpers import build_download_url, sanitize_filename

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}",
    response_model=CertificateMetadataResponse,
    summary="Get certificate metadata",
    description="Retrieve details and status for an individual certificate.",
)
def get_certificate_metadata(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    cert = job_service.get_certificate(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found",
        )

    res = CertificateMetadataResponse.model_validate(cert)
    if cert.status == CertificateStatus.COMPLETED:
        res.download_url = build_download_url(cert.id)

    if cert.job:
        res.title = cert.job.title
        res.course_name = cert.job.course_name
        res.issue_date = str(cert.job.issue_date)

    return res


@router.get(
    "/{certificate_id}/download",
    summary="Download generated certificate PDF",
    description="Download the generated PDF certificate for a recipient. Returns 404 if not found or not yet generated.",
)
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    cert = job_service.get_certificate(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found",
        )

    if cert.status != CertificateStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate is not ready for download. Current status: '{cert.status.value}'"
            + (f" (Reason: {cert.error_reason})" if cert.error_reason else ""),
        )

    if not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file record exists but storage path is missing",
        )

    try:
        filename = f"{cert.id}.pdf"
        file_path = storage_service.get_file_path(job_id=cert.job_id, filename=filename)
    except FileNotFoundError:
        logger.error("Certificate file %s missing on disk for job %s", filename, cert.job_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file is missing from storage",
        )
    except Exception as e:
        logger.error("Storage error retrieving certificate %s: %s", cert.id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving certificate file",
        )

    # Clean download filename for user convenience
    recipient_slug = sanitize_filename(cert.recipient_name)
    download_filename = f"Certificate_{recipient_slug}_{cert.id[:8]}.pdf"

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=download_filename,
    )
