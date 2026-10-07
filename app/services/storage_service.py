import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union
from app.core.config import settings
from app.core.logging import logger


class StorageException(Exception):
    """Base exception for storage operations."""
    pass


class InvalidPathException(StorageException):
    """Raised when an unsafe or invalid storage path is detected."""
    pass


class BaseStorageService(ABC):
    """Abstract interface for certificate file storage."""

    @abstractmethod
    def save_file(self, job_id: str, filename: str, content: bytes) -> str:
        """Save file bytes and return storage key/path."""
        pass

    @abstractmethod
    def get_file_path(self, job_id: str, filename: str) -> Path:
        """Get absolute path to stored file."""
        pass

    @abstractmethod
    def file_exists(self, job_id: str, filename: str) -> bool:
        """Check if file exists."""
        pass

    @abstractmethod
    def delete_file(self, job_id: str, filename: str) -> bool:
        """Delete a single file."""
        pass


class LocalStorageService(BaseStorageService):
    """Local filesystem implementation of storage service."""

    def __init__(self, base_dir: Union[str, Path, None] = None):
        self.base_dir = Path(base_dir).resolve() if base_dir else settings.storage_path
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_resolve(self, job_id: str, filename: str) -> Path:
        """
        Safely resolve file path preventing directory traversal attacks.
        Ensures the final path is strictly inside self.base_dir.
        """
        if not job_id or not filename:
            raise InvalidPathException("Job ID and filename cannot be empty")

        clean_job = job_id.strip()
        clean_file = filename.strip()

        # Reject path separators and parent directory traversal
        if ".." in clean_job or "/" in clean_job or "\\" in clean_job:
            logger.warning("Unsafe characters detected in job_id: %s", job_id)
            raise InvalidPathException("Unsafe characters in job ID")

        if ".." in clean_file or "/" in clean_file or "\\" in clean_file:
            logger.warning("Unsafe characters detected in filename: %s", filename)
            raise InvalidPathException("Unsafe characters in filename")

        target_dir = (self.base_dir / clean_job).resolve()
        target_path = (target_dir / clean_file).resolve()

        # Double check directory containment
        try:
            target_path.relative_to(self.base_dir)
        except ValueError:
            logger.error("Attempted path traversal attack: %s / %s", job_id, filename)
            raise InvalidPathException("Unsafe file path detected")

        return target_path

    def save_file(self, job_id: str, filename: str, content: bytes) -> str:
        """Save file bytes securely to local disk."""
        target_path = self._safe_resolve(job_id, filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            target_path.write_bytes(content)
            # Store relative path from base_dir for portability
            relative_path = str(target_path.relative_to(self.base_dir))
            logger.debug("Saved certificate to %s", target_path)
            return relative_path
        except Exception as e:
            logger.error("Failed to write certificate file: %s", str(e))
            raise StorageException(f"Failed to write certificate file: {str(e)}") from e

    def get_file_path(self, job_id: str, filename: str) -> Path:
        """Retrieve absolute path to stored file."""
        target_path = self._safe_resolve(job_id, filename)
        if not target_path.exists() or not target_path.is_file():
            raise FileNotFoundError(f"File not found: {filename} in job {job_id}")
        return target_path

    def file_exists(self, job_id: str, filename: str) -> bool:
        """Check if file exists on disk."""
        try:
            target_path = self._safe_resolve(job_id, filename)
            return target_path.exists() and target_path.is_file()
        except InvalidPathException:
            return False

    def delete_file(self, job_id: str, filename: str) -> bool:
        """Delete stored file if it exists."""
        try:
            target_path = self._safe_resolve(job_id, filename)
            if target_path.exists():
                target_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete file %s: %s", filename, str(e))
            return False

    def delete_job_dir(self, job_id: str) -> bool:
        """Delete all files for a job."""
        clean_job_id = os.path.basename(job_id.strip())
        target_dir = (self.base_dir / clean_job_id).resolve()
        try:
            target_dir.relative_to(self.base_dir)
            if target_dir.exists() and target_dir.is_dir():
                shutil.rmtree(target_dir)
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete directory for job %s: %s", job_id, str(e))
            return False


# Default storage singleton
storage_service = LocalStorageService()
