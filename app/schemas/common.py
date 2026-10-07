from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
