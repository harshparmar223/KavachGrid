"""
KAVACHGRID 3.0 — Database Engine & Session Factory
Phase 2: Complete Implementation

Provides:
    - SQLAlchemy engine (async-compatible)
    - Session factory (SessionLocal)
    - Declarative Base for all ORM models
    - get_db() dependency for FastAPI
    - init_db() for table creation
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""

    pass


# ============================================
# Database Engine
# ============================================
# Uses connection pooling with sensible defaults for a prototype
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,          # Max persistent connections
    max_overflow=20,       # Max temporary connections beyond pool_size
    pool_timeout=30,       # Seconds to wait for a connection from pool
    pool_recycle=1800,     # Recycle connections after 30 minutes
    pool_pre_ping=True,    # Verify connections before use (handles DB restarts)
    echo=settings.DEBUG,   # Log SQL statements in debug mode
)


# ============================================
# Session Factory
# ============================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================
# Dependency — Database Session
# ============================================
def get_db():
    """
    FastAPI dependency that provides a database session.

    Usage in route handlers:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...

    The session is automatically closed after the request completes,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# Database Initialization
# ============================================
def init_db():
    """
    Create all tables defined in the ORM models.

    This is used for initial setup and development.
    In production, use Alembic migrations instead.
    """
    # Import all models so they are registered with Base.metadata
    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully.")


def drop_db():
    """
    Drop all tables. USE WITH CAUTION — destroys all data.
    Only for development/testing.
    """
    import app.db.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped.")
