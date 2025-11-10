"""Database configuration and session management for SQLite."""

import logging
import os
from pathlib import Path
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from src.core.config import settings

logger = logging.getLogger(__name__)

# Database URL from settings (defaults to SQLite)
DATABASE_URL = settings.database_url

# Ensure data directory exists for SQLite
if DATABASE_URL.startswith("sqlite"):
    # Handle both relative and absolute paths
    db_path = DATABASE_URL.replace("sqlite:///", "")
    
    # Convert to Path object for better path handling
    db_file = Path(db_path)
    
    # Create parent directory if it doesn't exist
    if db_file.parent and str(db_file.parent) != ".":
        db_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created database directory: {db_file.parent}")

# Create engine with appropriate settings for SQLite
engine = create_engine(
    DATABASE_URL,
    echo=settings.debug,  # Log SQL queries in debug mode
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    # For SQLite, we don't need connection pooling
    poolclass=None if DATABASE_URL.startswith("sqlite") else None
)


def create_db_and_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def get_session() -> Generator[Session, None, None]:
    """
    Get database session.
    Use as dependency in FastAPI endpoints.
    """
    with Session(engine) as session:
        yield session


def get_db_session() -> Session:
    """
    Get database session for non-FastAPI usage.
    Remember to close the session when done.
    """
    return Session(engine)
