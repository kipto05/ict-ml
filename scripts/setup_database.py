# ============================================================================
# scripts/setup_database.py - Database Setup Script
# ============================================================================

"""
Database initialization and setup script.
Creates tables, seeds initial data, and validates connections.
"""

import sys
import os
from pathlib import Path

# Add project root to path
# sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.connection import db_manager, Base
from database.models import Account, Trade, DailyMetrics, MLModel
from config.settings import settings
from src.core.logger import main_logger
import click
from sqlalchemy import text

logger = main_logger


@click.group()
def cli():
    """Database management CLI."""
    pass


@cli.command()
def create():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        db_manager.create_tables()
        logger.info("✓ Database tables created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        sys.exit(1)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to drop all tables?')
def drop():
    """Drop all database tables."""
    try:
        logger.info("Dropping database tables...")
        db_manager.drop_tables()
        logger.info("✓ Database tables dropped successfully")
    except Exception as e:
        logger.error(f"✗ Failed to drop tables: {e}")
        sys.exit(1)


@cli.command()
def reset():
    """Reset database (drop and recreate)."""
    try:
        logger.info("Resetting database...")
        db_manager.drop_tables()
        db_manager.create_tables()
        logger.info("✓ Database reset successfully")
    except Exception as e:
        logger.error(f"✗ Failed to reset database: {e}")
        sys.exit(1)


@cli.command()
def seed():
    """Seed database with initial data."""
    try:
        logger.info("Seeding database...")

        with db_manager.get_session() as session:
            # Check if account already exists
            existing_account = session.query(Account).filter_by(
                login=settings.mt5_login
            ).first()

            if not existing_account:
                # Create default account
                account = Account(
                    login=settings.mt5_login,
                    server=settings.mt5_server,
                    balance=10000.0,
                    equity=10000.0,
                    leverage=100,
                    account_type="demo",
                    is_active=True
                )
                session.add(account)
                logger.info(f"✓ Created account: {settings.mt5_login}")
            else:
                logger.info(f"Account {settings.mt5_login} already exists")

        logger.info("✓ Database seeding completed")

    except Exception as e:
        logger.error(f"✗ Failed to seed database: {e}")
        sys.exit(1)


@cli.command()
def status():
    """Check database connection and table status."""
    try:
        logger.info("Checking database status...")

        # Test connection
        with db_manager.get_session() as session:
            result = session.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")

        # Check tables
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()

        logger.info(f"\nDatabase: {settings.db_name}")
        logger.info(f"Host: {settings.db_host}:{settings.db_port}")
        logger.info(f"\nTables ({len(tables)}):")
        for table in tables:
            logger.info(f"  - {table}")

    except Exception as e:
        logger.error(f"✗ Database check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()

