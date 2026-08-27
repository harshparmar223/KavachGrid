"""
KAVACHGRID 3.0 — Shared Dependencies
Phase 2: Database session dependency injection

Provides FastAPI dependencies for:
    - Database sessions
    - Current user authentication (Phase 5)
    - API key validation (Phase 9)
"""

from sqlalchemy.orm import Session

from app.db.database import get_db  # noqa: F401 — re-export for convenience

# Re-export get_db so routes can import from dependencies
# Usage: from app.dependencies import get_db
#
# @router.get("/items")
# def list_items(db: Session = Depends(get_db)):
#     ...

# TODO Phase 5: Add get_current_user dependency
# TODO Phase 9: Add verify_api_key dependency
