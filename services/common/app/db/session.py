import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sentilyzer_user:sentilyzer_password@localhost:5432/sentilyzer_db",
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL debugging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency function for FastAPI to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_session():
    """Create a database session for use outside of the FastAPI context.

    Remember to close the session after use.
    """
    return SessionLocal()


def get_db_engine():
    """Get the database engine for direct access."""
    return engine


def create_session():
    """Create a database session for scripts and utilities.

    Alias for create_db_session for consistency with generate_api_key.py.
    """
    return SessionLocal()
