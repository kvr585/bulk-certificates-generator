import re
from typing import Optional


def build_download_url(certificate_id: str, base_api_prefix: str = "/api/v1") -> str:
    """Build canonical download URL for a certificate."""
    return f"{base_api_prefix}/certificates/{certificate_id}/download"


def sanitize_filename(name: str) -> str:
    """
    Sanitize recipient or course name to be safe for Content-Disposition header.
    Removes invalid filesystem and header characters.
    """
    clean = re.sub(r"[^\w\s-]", "", name).strip()
    clean = re.sub(r"[-\s]+", "_", clean)
    return clean or "certificate"
