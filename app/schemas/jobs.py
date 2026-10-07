from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
from app.db.models import JobStatus
from app.schemas.certificates import RecipientCreate, CertificateResponse


class JobCreateRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Certificate title (e.g., Certificate of Completion)",
        examples=["Certificate of Completion"],
    )
    course_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the course, training, or event",
        examples=["Cloud Architecture & DevOps Masterclass"],
    )
    issuer_name: str = Field(
        default="Aereo Cloud Academy",
        min_length=1,
        max_length=255,
        description="Name of the issuing organization",
        examples=["Aereo Cloud Academy"],
    )
    issue_date: Optional[date] = Field(
        default_factory=date.today,
        description="Official issuance date (YYYY-MM-DD)",
        examples=["2026-10-07"],
    )
    recipients: List[RecipientCreate] = Field(
        ...,
        min_length=1,
        description="List of recipients to generate certificates for",
    )

    @field_validator("title", "course_name", "issuer_name")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or contain only whitespace")
        return stripped


class JobResponse(BaseModel):
    id: str
    title: str
    course_name: str
    issuer_name: str
    issue_date: date
    status: JobStatus
    total_count: int
    completed_count: int
    failed_count: int
    pending_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    @computed_field
    @property
    def progress_percentage(self) -> float:
        if self.total_count == 0:
            return 0.0
        processed = self.completed_count + self.failed_count
        return round((processed / self.total_count) * 100.0, 1)

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobResponse):
    certificates: Optional[List[CertificateResponse]] = None
