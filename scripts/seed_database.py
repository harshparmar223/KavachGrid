"""
KAVACHGRID 3.0 — Database Seeding Script
Phase 2: Run from project root

Usage:
    python scripts/seed_database.py

This script seeds the database with default users, devices,
and initial configuration for the SIH demo.
"""

import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.seed import seed_all

if __name__ == "__main__":
    seed_all()
