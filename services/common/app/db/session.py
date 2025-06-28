"""Database session management utilities."""


from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.common.app.config import DATABASE_URL
from services.common.app.logging_config import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# --- Database Engine and Session Management ---

def get_engine(database_url=None, **kwargs):
    """Create and return a new SQLAlchemy engine."""
    if database_url is None:
        database_url = DATABASE_URL
    return create_engine(database_url, **kwargs)

def get_session_factory(engine):
    """Create and return a new sessionmaker factory bound to the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db(SessionLocal=None):
    """Dependency function for FastAPI to get a database session."""
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = get_session_factory(engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_session(SessionLocal=None):
    """Create a database session for use outside of the FastAPI context.

    Remember to close the session after use.
    """
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = get_session_factory(engine)
    return SessionLocal()

def get_db_engine():
    """Get the database engine for direct access."""
    return get_engine()

def create_session(SessionLocal=None):
    """Create a database session for scripts and utilities.

    Alias for create_db_session for consistency with generate_api_key.py.
    """
    return create_db_session(SessionLocal=SessionLocal)
