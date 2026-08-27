# ⚡ KAVACHGRID 3.0

### AI-Powered Energy Theft, Anomaly Detection, Risk Ranking & Progressive Localization System

> **An Investigation Support System** that prioritizes inspections using multiple evidence signals.  
> *This system supports utility engineers with explainable, data-driven evidence ranking — it does NOT make unverified automated theft accusations.*

---

## 🎯 Overview

**KAVACHGRID 3.0** is an end-to-end smart grid monitoring and theft investigation support platform developed for the **Smart India Hackathon (SIH 2026)**. It detects unaccounted energy losses, consumption anomalies, meter tampering indicators, and communication degradation across distribution segments — computing **composite, explainable risk scores (0–100)** to help utility operators prioritize physical field inspections.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FIELD LAYER (ESP32)                           │
│  Feeder Node (INA226)    Consumer Meters (INA219)   Localization Nodes  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ MQTT over TLS (Port 8883/1883)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        COMMUNICATION & INGESTION                        │
│                   Mosquitto Broker (Topic ACLs & TLS)                   │
│                                    │                                    │
│                 FastAPI Async MQTT Subscriber (aiomqtt)                 │
│                                    │                                    │
│                   Topic Validation & Schema Decoder                     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             BACKEND & DATA                              │
│                    PostgreSQL 15 (Time-Series Data)                     │
│                                    │                                    │
│                 6 Analytics Engines (AI + Rules + Trust)                │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST & WebSockets
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION DASHBOARD                          │
│               Next.js 14 • MUI Dark Theme • Recharts • Leaflet          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📡 MQTT Topic Hierarchy

The communication layer follows a strict topic structure with topic validation and payload verification:

| Topic Pattern | Source Node | Purpose |
|---|---|---|
| `kavachgrid/feeder` | Feeder Node (ESP32 + INA226) | Total distribution transformer power & energy |
| `kavachgrid/feeder/{device_id}` | Named Feeder | Specific feeder segment readings |
| `kavachgrid/meter/{meter_id}` | Consumer Meter (ESP32 + INA219) | Household voltage, current, power, energy |
| `kavachgrid/localization/{zone_id}` | Localization Sensor (CT Clamp) | Branch/pole-level current for suspect ranking |
| `kavachgrid/alerts` | Edge & Backend Engines | Real-time threshold violations & tampering alarms |
| `kavachgrid/commands/{device_id}` | Backend / Dashboard | Remote node configuration & query commands |

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| **Field Devices** | ESP32, INA219, INA226, Current Transformer (CT) sensors, Embedded C++ |
| **Broker** | Eclipse Mosquitto (TLS 1.3, Topic-level ACLs, WebSockets) |
| **Backend** | Python 3.11+, FastAPI, `aiomqtt`, SQLAlchemy 2.0, Pydantic V2 |
| **Database** | PostgreSQL 15 |
| **AI / ML** | TensorFlow / Keras (Autoencoder Anomaly Detection), Scikit-Learn |
| **Frontend** | Next.js 14 (TypeScript), Material UI, Recharts, Leaflet.js |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

---

## 📦 Project Structure

```
KavachGrid/
├── ai/                # Autoencoder ML models & training pipelines
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # REST API route handlers
│   │   ├── db/        # SQLAlchemy PostgreSQL models & database engine
│   │   ├── engines/   # 6 Analytics engines (Energy Balance, Risk, etc.)
│   │   ├── mqtt/      # Async MQTT client, topics, and message handlers
│   │   ├── schemas/   # Pydantic validation models
│   │   ├── services/  # Business logic & DB ingestion pipelines
│   │   └── config.py  # Centralized environment settings
│   ├── tests/         # Pytest automated test suite
│   │   └── test_mqtt/ # Comprehensive MQTT unit & integration tests
│   └── requirements.txt
├── dashboard/         # Next.js frontend dashboard
├── docs/              # System architecture, database, API specifications
├── firmware/          # ESP32 firmware for Feeder, Consumer, and Localization nodes
├── mqtt/              # Mosquitto broker config, ACLs, and TLS certs
├── scripts/           # Demo scenarios, seed scripts, cert generators
├── simulator/         # Software-based grid node simulator
└── docker-compose.yml # Multi-container deployment specification
```

---

## 🚀 Getting Started

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18+ & npm
- **Docker & Docker Compose** (optional for containerized setup)
- **PostgreSQL 15** & **Mosquitto MQTT Broker**

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/lavleshydv/KavachGrid.git
cd KavachGrid

# Copy environment configuration
cp .env.example .env
```

### 2. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Run Automated Tests
```bash
cd backend
pytest tests -v
```

### 4. Firmware Setup (ESP32)
The project includes Arduino core firmware for three types of nodes:
- **Feeder Node (`firmware/feeder_node/feeder_node.ino`)**: ESP32 + INA226 (I2C)
- **Consumer Node (`firmware/consumer_node/consumer_node.ino`)**: ESP32 + INA219 (I2C)
- **Localization Node (`firmware/localization_node/localization_node.ino`)**: ESP32 + CT Clamp (ADC)

To deploy:
1. Open the `.ino` files in Arduino IDE or PlatformIO.
2. Install required libraries: `WiFi`, `PubSubClient`, `ArduinoJson`, `Adafruit_INA219`, `Adafruit_INA226`, and `EmonLib`.
3. Update `YOUR_WIFI_SSID` and `YOUR_WIFI_PASSWORD`.
4. Flash to the respective ESP32 boards.
*Refer to the `wiring_diagram.md` in each node's folder for hardware assembly instructions.*

---

## 🔐 Key Capabilities

- **⚡ Real-Time Energy Balancing** — Calculates instantaneous and aggregated unaccounted losses ($P_{\text{feeder}} - \sum P_{\text{consumers}}$).
- **🤖 AI Anomaly Detection** — Unsupervised autoencoder flags unusual power factor, load-shifting, and current anomalies.
- **🩺 Meter Health Engine** — Identifies sensor drift, frozen readings, impossible negative values, and communication drops.
- **🛡️ Zero-Trust Device Validation** — Rejects spoofed topics, mismatched payloads, and unauthorized device IDs.
- **🎯 KAVACH Risk Engine** — Calculates a weighted composite score ($0-100$) and categorizes risk into `Low`, `Medium`, `High`, and `Critical`.
- **📍 Progressive Localization** — Pinpoints high-loss distribution branches to narrow physical inspection zones.

---

## 👥 Team KAVACH (SIH 2026)

| Name | Role | Focus Area |
|---|---|---|
| **Lavlesh** | Backend & Database Engineer | FastAPI, MQTT Ingestion, PostgreSQL, Services |
| **Yash Sharma** | Team Lead / AI & Backend | System Architecture, Risk Engine, Energy Balance |
| **Harsh Parmar** | Hardware & Firmware Engineer | ESP32, Embedded C++, Mosquitto & TLS, Edge Analytics |
| **Abhishek Shrivastava** | AI/ML Engineer | Autoencoders, Anomaly Detection, Synthetic Dataset |
| **Nitin Rajak** | Frontend & Design Engineer | Next.js Dashboard, Risk Monitoring UI, Components |
| **Adya** | Frontend & Design Engineer | GIS Map Integration, Progressive Localization UI |

---

## 📄 License

Developed for the Smart India Hackathon 2026. All rights reserved.
