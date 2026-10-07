import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.api.deps import get_db
from app.core.config import settings
from app.db.database import Base
from app.main import app
from app.services.storage_service import LocalStorageService, storage_service

# Temporary test directory
TEST_DIR = Path(tempfile.mkdtemp(prefix="test_cert_storage_"))
TEST_DB_PATH = TEST_DIR / "test_certificates.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup and teardown for test session."""
    # Override storage directory
    test_storage_dir = TEST_DIR / "generated_certificates"
    test_storage_dir.mkdir(parents=True, exist_ok=True)
    storage_service.base_dir = test_storage_dir

    yield

    # Teardown test directory
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Creates fresh tables for each test and drops them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provides a transactional database session for unit tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient configured with dependency overrides for database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Also monkeypatch JobService to use TestingSessionLocal for background tasks
    import app.services.job_service as job_module
    original_session_local = job_module.SessionLocal
    job_module.SessionLocal = TestingSessionLocal

    with TestClient(app) as test_client:
        yield test_client

    job_module.SessionLocal = original_session_local
    app.dependency_overrides.clear()
