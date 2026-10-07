from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from app.db.models import CertificateStatus


class RecipientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of the certificate recipient")
    email: Optional[EmailStr] = Field(None, description="Optional email address of the recipient")
    custom_attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional key-value metadata (e.g., grade, honors, role)",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Recipient name cannot be empty or whitespace only")
        return stripped


class CertificateResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    status: CertificateStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    error_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    generated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CertificateMetadataResponse(CertificateResponse):
    """Certificate detail with associated job context."""
    title: Optional[str] = None
    course_name: Optional[str] = None
    issue_date: Optional[str] = None
