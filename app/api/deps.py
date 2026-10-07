from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

# Re-export get_db for convenient dependency injection
DbSession = Depends(get_db)
