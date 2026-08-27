"""
KAVACHGRID 3.0 — FastAPI Application Entry Point

This is the main application file that:
- Initializes the FastAPI app
- Registers all API routers
- Sets up CORS middleware
- Initializes the database on startup
- Handles graceful shutdown & MQTT background client
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db
from app.mqtt import mqtt_client, start_mqtt_client, stop_mqtt_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # ---- Startup ----
    print("=" * 60)
    print("⚡ KAVACHGRID 3.0 Backend starting...")
    print(f"📡 MQTT Broker: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
    print(f"🗄️  Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print("=" * 60)

    # Initialize database tables
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        print("   (This is normal if PostgreSQL is not running yet)")

    # Phase 3: Start async MQTT subscriber client in background
    try:
        await start_mqtt_client(app)
        print("✅ MQTT background subscriber started")
    except Exception as e:
        print(f"⚠️  MQTT background subscriber failed to start: {e}")

    yield

    # ---- Shutdown ----
    print("🛑 KAVACHGRID 3.0 Backend shutting down...")
    # Phase 3: Stop MQTT subscriber
    try:
        await stop_mqtt_client(app)
        print("✅ MQTT subscriber stopped gracefully")
    except Exception as e:
        print(f"⚠️  Error stopping MQTT subscriber: {e}")


app = FastAPI(
    title="KAVACHGRID 3.0",
    description=(
        "AI-Powered Energy Theft, Anomaly Detection, "
        "Risk Ranking & Progressive Localization System. "
        "An Investigation Support System that prioritizes inspections "
        "using multiple evidence signals."
    ),
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "KAVACHGRID 3.0",
        "status": "operational",
        "version": "3.0.0",
        "description": "AI-Powered Energy Theft Investigation Support System",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check with service statuses."""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "mqtt": mqtt_client.status_summary,
            "ai_engine": "pending",     # Phase 8
            "risk_engine": "pending",   # Phase 10
        },
    }
