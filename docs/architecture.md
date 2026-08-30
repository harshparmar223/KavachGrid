# 🏗️ KavachGrid — Architecture Deep Dive

### High-Integrity Zero-Trust Smart Grid Anomaly Detection & Investigation Support Platform

---

## 1. System Philosophy & Objectives
KavachGrid is designed as a **Decision-Support and Investigation Platform** for Power Distribution Companies (DISCOMs). It solves the fundamental limitations of traditional anti-theft operations:
1. **Elimination of Unverified Automated Accusations:** Under Indian utility regulations, criminal penalties cannot be assessed without physical verification. KAVACHGRID generates actionable, statistically ranked evidence dossiers for field inspection squads.
2. **Decoupling Grid Physics from Commercial Fraud:** Decouples technical line losses ($I^2R$, transformer eddy currents) and hardware sensor failures from deliberate bypass theft.
3. **Zero Trust Cryptographic and Physical Verification:** Verifies the physical consistency of telemetry ($P \approx V \cdot I \cdot PF$) to prevent forged packet injection.

---

## 2. 6-Tier Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TIER 1: PHYSICAL & EDGE SENSING                  │
│   Feeder Substation (ESP32 + INA226)    Consumer Meters (ESP32 + INA219)│
│                        Branch Localization Nodes                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ MQTT 3.1.1 / TLS (Port 8883/1883)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     TIER 2: SECURE COMMUNICATION BROKER                 │
│          Eclipse Mosquitto 2.0 (Topic ACLs, TLS Certificates)           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Async TCP Streams
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   TIER 3: ASYNC INGESTION & ZERO TRUST                  │
│       FastAPI Ingestion Worker (aiomqtt) + Topic Regex Validation       │
│               4-Pillar Zero Trust Physics Validation Engine             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ SQLAlchemy ORM
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       TIER 4: MULTI-ENGINE ANALYTICS                    │
│   • Energy Balance Engine (5% Decoupling)   • Neural Autoencoder (MSE)  │
│   • Meter Health Engine (0-100 Variance)    • 5-Pillar Risk Engine      │
│   • Progressive Localization Engine (Zone Candidate Narrowing)          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│     TIER 5: DATA PERSISTENCE      │ │    TIER 6: PRESENTATION & WS      │
│ PostgreSQL 15 Relational Schema   │ │ Next.js 14 Dashboard Console      │
│ (7 Relational/Timeseries Tables)  │ │ Real-Time WebSocket Broadcast     │
└───────────────────────────────────┘ └───────────────────────────────────┘
```

---

## 3. The 6 Analytics Engines Detailed

### Stage 1: Zero Trust Physics Engine (`device_trust.py`)
* Evaluates 4 pillars on every ingested packet:
  1. Identity match in database (30%)
  2. Topic ACL authorization match (25%)
  3. Power equation physical plausibility $P \approx V \cdot I \cdot PF$ (30%)
  4. Temporal timestamp validity $\Delta t < 120\text{s}$ (15%)

### Stage 2: Energy Balance Engine (`energy_balance.py`)
* Calculates true transformer grid load balance:
  $$\Delta P = P_{\text{feeder}} - \sum P_{\text{consumer}} - P_{\text{technical\_loss}}$$
* Deducts $5\%$ baseline line resistance loss.
* Exponential loss-to-severity mapping (`low`, `medium`, `high`, `critical`).

### Stage 3: AI Neural Autoencoder (`ai_anomaly.py`)
* TensorFlow/Keras deep autoencoder trained on diurnal residential load curves.
* Calculates Reconstruction Mean Squared Error (MSE).
* Normalizes to $0.0–1.0$ anomaly score with dynamic time-of-day thresholds.

### Stage 4: Meter Health Engine (`meter_health.py`)
* Evaluates packet completeness, interval jitter, and sensor variance ($\sigma^2$).
* Detects frozen/stuck readings and generates **Maintenance Work Orders** instead of false theft accusations.

### Stage 5: Composite Risk Engine (`risk_engine.py`)
* Computes explainable 5-factor weighted risk:
  $$\text{Risk Score} = 0.30(E) + 0.25(A) + 0.20(100 - H) + 0.15(100 - T) + 0.10(100 - C)$$
* Ranks suspects into 4 severity tiers with human-readable audit explanations.

### Stage 6: Progressive Localization Engine (`localization.py`)
* Cross-references branch current monitor CT clamps with downstream suspect rankings in `ZONE-A`.
* Computes localization confidence ($0–100\%$) and outputs actionable inspection orders.
