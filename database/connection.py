# ============================================================================
# database/connection.py - Database Connection Management
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from config.settings import settings
from src.core.logger import main_logger
from database.models import Base

logger = main_logger


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        logger.info(f"Database connection initialized: {self.database_url.split('@')[1]}")

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_db(self) -> Generator[Session, None, None]:
        """
        Dependency for FastAPI endpoints.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()