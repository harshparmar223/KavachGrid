# ⚡ KAVACHGRID 3.0

### AI-Powered Energy Theft, Anomaly Detection, Risk Ranking & Progressive Localization System

> **An Investigation Support System** that prioritizes inspections using multiple evidence signals.
> This system does NOT claim to automatically prove theft.

---

## 🎯 Overview

KAVACHGRID 3.0 is a complete end-to-end smart grid monitoring platform designed for the **Smart India Hackathon (SIH)**. It detects unexplained energy losses, abnormal consumption patterns, meter tampering indicators, and communication failures — then generates **explainable risk scores** to help utility operators prioritize field inspections.

## 🏗️ Architecture

```
ESP32 + Sensors → MQTT Broker → FastAPI Backend → PostgreSQL
                                      ↓
                              Analytics Engine
                                      ↓
                                 AI Engine
                                      ↓
                                Risk Engine
                                      ↓
                                Dashboard
```

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Hardware** | ESP32, INA219/INA226 sensors |
| **Communication** | MQTT (Mosquitto) with TLS |
| **Backend** | Python, FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL |
| **AI/ML** | TensorFlow, Keras, Scikit-Learn |
| **Frontend** | Next.js, TypeScript, Material UI, Recharts, Leaflet.js |
| **Deployment** | Docker, Docker Compose |

## 📦 Project Structure

```
KavachAI/
├── firmware/          # ESP32 embedded code (C++)
├── mqtt/              # Mosquitto broker configuration
├── backend/           # FastAPI backend + analytics engines
├── ai/                # AI/ML training & inference pipeline
├── dashboard/         # Next.js frontend dashboard
├── simulator/         # Software-based node simulator
├── scripts/           # Demo & utility scripts
└── docs/              # Project documentation
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Arduino IDE (for firmware flashing)

### One-Command Launch
```bash
docker-compose up --build
```

### Access Points
| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| MQTT Broker | mqtt://localhost:1883 |

## 🧪 Demo Mode

Run the software simulator for SIH demonstrations (no hardware needed):
```bash
python scripts/demo_scenarios.py
```

## 🔐 Key Features

- **Energy Balance Monitoring** — Detects unaccounted energy losses
- **AI Anomaly Detection** — Autoencoder-based consumption pattern analysis
- **Meter Health Scoring** — Detects stuck readings, sensor drift, communication failures
- **Device Trust Validation** — Zero Trust-inspired payload verification
- **KAVACH Risk Engine** — Weighted composite scoring (0-100)
- **Progressive Localization** — Narrows investigation areas with confidence scoring
- **Real-time Dashboard** — Live monitoring with WebSocket updates
- **GIS Visualization** — Risk-mapped geographic view

## 📄 License

This project is developed for SIH 2026. All rights reserved.

## 👥 Team

**Team KAVACH** — Smart India Hackathon 2026
