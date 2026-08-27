"""
KAVACHGRID 3.0 — Database Seeding
Phase 2: Initial data seeding for development and demo

Seeds:
    1. Default admin user
    2. Feeder node device
    3. Consumer node devices (H1-H4)
    4. Localization node device (optional)

Usage:
    From backend directory:
        python -m app.db.seed

    Or via script:
        python scripts/seed_database.py
"""

import uuid
import secrets

from sqlalchemy.orm import Session

from app.db.database import SessionLocal, init_db
from app.db.models import Device, User


def generate_api_key() -> str:
    """Generate a secure random API key for device authentication."""
    return f"kavach_{secrets.token_hex(16)}"


def seed_users(db: Session) -> None:
    """Seed default users."""

    # Check if admin already exists
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print("  ⏭️  Users already seeded, skipping...")
        return

    users = [
        User(
            username="admin",
            email="admin@kavachgrid.in",
            hashed_password="$2b$12$placeholder_hash_replace_in_phase5",
            full_name="System Administrator",
            role="admin",
            is_active=True,
        ),
        User(
            username="operator1",
            email="operator1@kavachgrid.in",
            hashed_password="$2b$12$placeholder_hash_replace_in_phase5",
            full_name="Grid Operator",
            role="operator",
            is_active=True,
        ),
        User(
            username="investigator1",
            email="investigator1@kavachgrid.in",
            hashed_password="$2b$12$placeholder_hash_replace_in_phase5",
            full_name="Field Investigator",
            role="investigator",
            is_active=True,
        ),
    ]

    for user in users:
        db.add(user)

    db.commit()
    print(f"  ✅ Seeded {len(users)} users")


def seed_devices(db: Session) -> None:
    """Seed default devices for the prototype grid."""

    # Check if devices already exist
    existing = db.query(Device).filter(Device.device_id == "FEEDER-01").first()
    if existing:
        print("  ⏭️  Devices already seeded, skipping...")
        return

    devices = [
        # Feeder Node — measures total energy entering the distribution segment
        Device(
            device_id="FEEDER-01",
            device_type="feeder",
            name="Main Feeder Node",
            location="Distribution Transformer DT-001",
            latitude=28.6139,   # New Delhi coordinates (demo)
            longitude=77.2090,
            api_key=generate_api_key(),
            status="offline",
            zone_id="ZONE-A",
            device_metadata={
                "hardware": "ESP32 + INA226",
                "firmware_version": "3.0.0",
                "max_current": 30.0,
                "shunt_resistor": 0.1,
            },
        ),
        # Consumer Nodes — individual household meters
        Device(
            device_id="CONSUMER-H1",
            device_type="consumer",
            name="House 1 — Sharma Residence",
            location="Plot 101, Sector 5",
            latitude=28.6145,
            longitude=77.2095,
            api_key=generate_api_key(),
            status="offline",
            zone_id="ZONE-A",
            device_metadata={
                "hardware": "ESP32 + INA219",
                "firmware_version": "3.0.0",
                "max_current": 15.0,
                "sanctioned_load_kw": 3.0,
            },
        ),
        Device(
            device_id="CONSUMER-H2",
            device_type="consumer",
            name="House 2 — Patel Residence",
            location="Plot 102, Sector 5",
            latitude=28.6148,
            longitude=77.2092,
            api_key=generate_api_key(),
            status="offline",
            zone_id="ZONE-A",
            device_metadata={
                "hardware": "ESP32 + INA219",
                "firmware_version": "3.0.0",
                "max_current": 15.0,
                "sanctioned_load_kw": 2.5,
            },
        ),
        Device(
            device_id="CONSUMER-H3",
            device_type="consumer",
            name="House 3 — Kumar Residence",
            location="Plot 103, Sector 5",
            latitude=28.6142,
            longitude=77.2088,
            api_key=generate_api_key(),
            status="offline",
            zone_id="ZONE-A",
            device_metadata={
                "hardware": "ESP32 + INA219",
                "firmware_version": "3.0.0",
                "max_current": 15.0,
                "sanctioned_load_kw": 3.0,
            },
        ),
        Device(
            device_id="CONSUMER-H4",
            device_type="consumer",
            name="House 4 — Singh Residence",
            location="Plot 104, Sector 5",
            latitude=28.6150,
            longitude=77.2098,
            api_key=generate_api_key(),
            status="offline",
            zone_id="ZONE-A",
            device_metadata={
                "hardware": "ESP32 + INA219",
                "firmware_version": "3.0.0",
                "max_current": 15.0,
                "sanctioned_load_kw": 2.0,
            },
        ),
        # Localization Node — current clamp for zone-level monitoring
        Device(
            device_id="LOC-ZONE-A",
            device_type="localization",
            name="Localization Node — Zone A",
            location="Pole #7, Sector 5 Branch",
            latitude=28.6146,
            longitude=77.2091,
            api_key=generate_api_key(),
            status="offline",
            zone_id="ZONE-A",
            device_metadata={
                "hardware": "ESP32 + CT Clamp",
                "firmware_version": "3.0.0",
                "ct_ratio": 100,
                "burden_resistor": 33.0,
            },
        ),
    ]

    for device in devices:
        db.add(device)

    db.commit()
    print(f"  ✅ Seeded {len(devices)} devices")


def seed_all():
    """Run all seeders."""
    print("\n🌱 KAVACHGRID 3.0 — Database Seeding")
    print("=" * 50)

    # Ensure tables exist
    init_db()

    db = SessionLocal()
    try:
        seed_users(db)
        seed_devices(db)
        print("=" * 50)
        print("🌱 Seeding complete!\n")
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
