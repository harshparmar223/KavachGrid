# 🚢 KavachGrid — Deployment & Production Guide

---

## 1. Local Development Mode

### One-Click Launch (Recommended):
```powershell
python start.py
```
*Starts FastAPI backend on port 8000 and Next.js frontend on port 3000, and auto-opens your default browser.*

---

## 2. Multi-Container Docker Deployment

To launch the full containerized stack including PostgreSQL, Mosquitto MQTT, FastAPI, and Next.js:

```powershell
# 1. Generate TLS Certificates (optional for production TLS)
bash scripts/generate_certs.sh

# 2. Build and start all 4 services
docker-compose up -d --build

# 3. Verify container health
docker-compose ps
```

### Container Port Mapping:
* **PostgreSQL 15:** Port `5432`
* **Mosquitto MQTT:** Port `1883` (Plain), `8883` (TLS), `9001` (WebSockets)
* **FastAPI Backend:** Port `8000`
* **Next.js Dashboard:** Port `3000`

---

## 3. Environment Configuration (`.env`)

Copy `.env.example` to `.env` and configure production parameters:
```ini
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kavachgrid
POSTGRES_USER=kavach_admin
POSTGRES_PASSWORD=your_secure_password

# FastAPI
SECRET_KEY=your_random_jwt_secret_key
API_KEY=kavach-device-api-key

# MQTT Broker
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=kavachgrid_backend
MQTT_PASSWORD=kavachgrid
```
