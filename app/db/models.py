import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Date, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class CertificateStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    title = Column(String(255), nullable=False)
    course_name = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False, default="Aereo Cloud Academy")
    issue_date = Column(Date, nullable=False)

    status = Column(
        Enum(JobStatus, native_enum=False, length=32),
        nullable=False,
        default=JobStatus.QUEUED,
        index=True,
    )

    total_count = Column(Integer, nullable=False, default=0)
    completed_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    pending_count = Column(Integer, nullable=False, default=0)

    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    certificates = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="Certificate.created_at",
    )


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    job_id = Column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True, index=True)
    custom_attributes = Column(JSON, nullable=True)

    status = Column(
        Enum(CertificateStatus, native_enum=False, length=32),
        nullable=False,
        default=CertificateStatus.PENDING,
        index=True,
    )

    file_path = Column(String(512), nullable=True)
    file_size = Column(Integer, nullable=True)
    error_reason = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    generated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("Job", back_populates="certificates")
