"""
KAVACHGRID 3.0 — Database Engine & Session Factory
Phase 2: Complete Implementation with Automatic PostgreSQL & SQLite Fallback

Provides:
    - SQLAlchemy engine (PostgreSQL with graceful SQLite fallback)
    - Session factory (SessionLocal)
    - Declarative Base for all ORM models
    - get_db() dependency for FastAPI
    - init_db() for table creation and automatic seeding
"""

import io
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "buffer") and sys.stdout.encoding != "utf-8":
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "buffer") and sys.stderr.encoding != "utf-8":
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""

    pass


# ============================================
# Database Engine Initialization
# ============================================
def create_app_engine():
    """
    Attempts to initialize PostgreSQL engine.
    If PostgreSQL is unavailable or refuses connection, seamlessly falls back to SQLite.
    """
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql"):
        try:
            # Test direct connection to PostgreSQL
            pg_engine = create_engine(
                db_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=3,
                pool_recycle=1800,
                pool_pre_ping=True,
                echo=False,
            )
            with pg_engine.connect() as conn:
                print("🗄️  Database: PostgreSQL connected (port 5432)")
            return pg_engine
        except Exception:
            print("🗄️  Database: SQLite active (kavachgrid.db)")

    # SQLite fallback
    sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "kavachgrid.db"))
    sqlite_url = f"sqlite:///{sqlite_path}"
    sqlite_engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    return sqlite_engine


engine = create_app_engine()

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
    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# Database Initialization & Seeding
# ============================================
def init_db():
    """
    Create all tables defined in the ORM models and auto-seed if empty.
    """
    import app.db.models  # noqa: F401
    from app.db.models import Device, User
    from app.db.seed import seed_devices, seed_users

    Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified/created successfully.")

    # Auto-seed devices & users if empty
    db = SessionLocal()
    try:
        if not db.query(Device).first() or not db.query(User).first():
            print("🌱 Seeding initial devices and users into database...")
            seed_users(db)
            seed_devices(db)
    except Exception as e:
        print(f"⚠️  Auto-seed notice: {e}")
    finally:
        db.close()


def drop_db():
    """
    Drop all tables. USE WITH CAUTION — destroys all data.
    Only for development/testing.
    """
    import app.db.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped.")
