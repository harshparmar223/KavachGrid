# ⚡ KavachGrid

### AI-Powered Zero-Trust Smart Grid Energy Theft, Anomaly Detection & Progressive Localization System

> **An Investigation Support System for Power Distribution Utilities (DISCOMs)**  
> *Developed for the Smart India Hackathon (SIH 2026) — Hardware Category with Scale Simulation Engine.*  
> **Core Philosophy:** *Supports utility engineers with explainable, data-driven evidence ranking — it does NOT make unverified automated theft accusations.*

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#-1-executive-summary--problem-statement)
2. [How It Works: Technical vs. Layman Breakdown (Side-by-Side)](#-2-how-it-works-technical-vs-layman-breakdown-side-by-side)
3. [Technology Stack & Frameworks Used](#-3-technology-stack--frameworks-used)
4. [Master Function Catalog & API Reference](#-4-master-function-catalog--api-reference)
   - [4.1. Core Analytics Engines](#41-core-analytics-engines)
   - [4.2. MQTT Ingestion & Message Routing](#42-mqtt-ingestion--message-routing)
   - [4.3. FastAPI REST Endpoints & WebSocket](#43-fastapi-rest-endpoints--websocket)
   - [4.4. Virtual Grid Simulator Classes](#44-virtual-grid-simulator-classes)
   - [4.5. Embedded C++ Firmware Functions](#45-embedded-c-firmware-functions)
5. [The 6 SIH Demo Scenarios](#-5-the-6-sih-demo-scenarios)
6. [Quickstart & 1-Click Execution](#-6-quickstart--1-click-execution)
7. [Testing & Verification](#-7-testing--verification)

---

## 🎯 1. Executive Summary & Problem Statement

### The Problem
Indian Power Distribution Companies (DISCOMs) lose over **₹30,000 Crores annually** due to Aggregate Technical and Commercial (AT&C) losses, primarily driven by **direct line hooking, neutral bypasses, meter firmware tampering, and compromised telemetry**. Traditional physical raid squads have a **< 15% success rate** because offenders easily detach bypass hooks before inspections, resulting in wasted manpower, customer harassment, and revenue hemorrhage.

### The Solution: KavachGrid
KavachGrid is a 6-layer defense system that deploys intelligent edge sensing on distribution transformers and smart meters, backed by cloud multi-signal evidence fusion. It continuously correlates energy balance with neural reconstruction anomalies, device trust signatures, and hardware health metrics — computing an **Explainable Composite Risk Score (0–100)** to pinpoint suspect theft nodes with high statistical confidence.

---

## 🔄 2. How It Works: Technical vs. Layman Breakdown (Side-by-Side)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   END-TO-END WORKFLOW PIPELINE                                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [ESP32 Smart Meters] ──► [Mosquitto TLS Broker] ──► [FastAPI Async Ingestion (aiomqtt)]          │
│                                                                   │                              │
│                                                                   ▼                              │
│   ┌──────────────────────────────────────────────────────────────────────────────┐               │
│   │                        6-STAGE ANALYTICS PIPELINE                            │               │
│   │ 1. Zero Trust Physics Check   ──► 2. Energy Balance (5% Technical Decouple)  │               │
│   │ 3. Neural Autoencoder MSE     ──► 4. Meter Health & Drift Analysis           │               │
│   │ 5. 5-Pillar Risk Engine       ──► 6. Progressive Localization (Zone A Focus) │               │
│   └──────────────────────────────────────────────────────────────────────────────┘               │
│                                           │                                                      │
│                                           ▼                                                      │
│   [PostgreSQL 15 Timeseries DB] ◄───► [WebSocket Broadcast] ──► [Next.js Control Room Dashboard]│
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

| System Stage | 🔬 Technical Architecture & Physics Workflow | 💡 Plain English / Layman Explanation |
|---|---|---|
| **1. Field Telemetry Ingestion** | ESP32 nodes sample $V_{rms}$, $I_{rms}$, Active Power ($P$), Apparent Power ($S$), Power Factor ($PF$), and Frequency ($f$) at 5-second intervals via I2C from INA226/INA219 sensors, transmitting JSON over MQTT/TLS. | Think of this as the "digital pulse" of every house and transformer. Smart sensors read electricity speed and volume every 5 seconds and send it securely over the internet. |
| **2. Zero Trust & Physical Plausibility** | The `DeviceTrustEngine` validates $P \approx V \times I \times PF$ within a $15\%$ tolerance, checks topic authorization in `acl.conf`, and penalizes timestamp replays or future drift ($>120\text{s}$). | Checks if anyone is trying to "fake" their bill. If someone claims they used only 100W, but their voltage is 230V and current is 5A (which equals 1150W), the system catches the lie immediately using basic physics ($P=V \times I$). |
| **3. Energy Balance & Loss Decoupling** | The `EnergyBalanceEngine` decouples natural $I^2R$ technical losses ($\alpha = 5\%$) from the transformer input. The unaccounted deficit $\Delta P = P_{\text{feeder}} - \sum P_{\text{meters}} - P_{\text{technical}}$ is converted to an exponential severity score. | When electricity flows down a street, some energy is naturally lost as wire heat (about 5%). The system deducts this normal loss first. If a huge gap still remains, it knows someone is stealing power directly from the overhead line. |
| **4. AI Autoencoder Anomaly Detection** | A TensorFlow/Keras Neural Autoencoder maps temporal load vectors $\mathbf{x} = [V, I, P, PF, \text{Hour}, \text{Day}]$ to a latent space. Reconstruction MSE $> \text{threshold}$ indicates abnormal consumption deviations uncharacteristic of human residential patterns. | The AI learns a family's daily habits (sleeping at night, AC on in summer). If a factory starts running secretly in a house, or if the meter suddenly drops to near-zero while neighbors are using power, the AI spots the unnatural pattern. |
| **5. Meter Health vs. Theft Decoupling** | The `MeterHealthEngine` evaluates sensor variance $\sigma^2$, communication dropout count, and stuck reading counts (0–100 score). Low variance ($\sigma^2 < 0.001$) triggers a hardware fault, **preventing false theft accusations**. | **Zero False Accusation Guarantee:** If a meter breaks or freezes, an ordinary system might call the customer a thief. KAVACHGRID detects the broken sensor and sends a **Repair Technician** instead of a police raid squad. |
| **6. Composite Risk Engine & Localization** | Fuses 5 pillars into a single score: $\text{Risk} = 0.30(E) + 0.25(A) + 0.20(100-H) + 0.15(100-T) + 0.10(100-C)$. Ranks candidate consumers in `ZONE-A` and generates automated investigation actions. | Combines all 5 evidence clues into a final 0–100 "Guilt Score" and tells utility officers: *"Go to Street 4, Pole 2, House H2 — there is an 86% probability of theft with 1.3 kW unaccounted draw."* |

---

## 🛠️ 3. Technology Stack & Frameworks Used

| Layer | Framework / Library | Version | Exact Purpose in KavachGrid |
|---|---|---|---|
| **Embedded Firmware** | **Arduino C++ / ESP-IDF** | Core 3.0+ | Microcontroller firmware runtime for ESP32 DevKit v1 |
| | **Adafruit_INA226 / INA219** | v1.1.0 | I2C driver for high-side voltage, current, and wattage acquisition |
| | **PubSubClient** | v2.8.0 | Lightweight embedded MQTT client with TLS socket support |
| | **ArduinoJson** | v6.21.0 | Fast on-chip JSON serialization/deserialization |
| **Messaging & Broker** | **Eclipse Mosquitto** | v2.0.18 | High-throughput MQTT message broker (Ports 1883, 8883 TLS, 9001 WS) |
| | **aiomqtt** | v2.5.1 | Python async context-managed MQTT client for non-blocking ingestion |
| | **paho-mqtt** | v2.1.0 | Synchronous fallback and Python simulator transport adapter |
| **Backend Core** | **FastAPI** | v0.104.1 | Modern, high-performance async Web API framework |
| | **Uvicorn** | v0.24.0 | Lightning-fast ASGI web server with hot-reloading |
| | **SQLAlchemy** | v2.0.23 | Declarative Object-Relational Mapper (ORM) for PostgreSQL |
| | **PostgreSQL** | v15.0 | Relational and time-series database engine (7 relational tables) |
| | **Pydantic v2** | v2.5.2 | Strict schema validation, serialization, and typing |
| | **Alembic** | v1.13.0 | Database schema migration and version control manager |
| | **python-jose** | v3.3.0 | JWT (JSON Web Token) authentication and signature verification |
| | **passlib (bcrypt)** | v1.7.4 | Cryptographic password hashing for utility operators |
| **AI / Machine Learning** | **TensorFlow / Keras** | v2.15.0 | Neural Autoencoder architecture for reconstruction MSE anomaly detection |
| | **Scikit-Learn** | v1.3.2 | StandardScaler normalization pipelines and evaluation metrics |
| | **NumPy & Pandas** | v1.26 / 2.1 | Numerical matrix math and temporal load-profile manipulation |
| **Frontend Dashboard** | **Next.js (App Router)** | v14.2.35 | Server-rendered React framework with dynamic routing |
| | **React** | v18.2.0 | Reactive component UI library |
| | **Material UI (MUI)** | v5.15.0 | Sleek dark-mode design system with responsive typography |
| | **Recharts** | v2.15.4 | Interactive SVG composable charts (Energy Balance, MSE Timelines) |
| | **OGL** | v1.0.11 | Minimal WebGL library for GPU-accelerated animated Galaxy backdrop |
| | **GSAP** | v3.15.0 | GreenSock Animation Platform for FoldText typography transitions |
| | **Axios** | v1.6.0 | HTTP client with automatic fallback data stores |
| **Testing & Tools** | **Pytest & pytest-asyncio** | v8.3.5 | Automated test runner executing 60/60 unit test suite |
| | **Docker & Compose** | v3.8 | Multi-container orchestration (DB, Mosquitto, API, UI) |

---

## 📖 4. Master Function Catalog & API Reference

### 4.1. Core Analytics Engines

#### ⚡ `EnergyBalanceEngine` ([`backend/app/engines/energy_balance.py`](file:///c:/Users/HP/KavachAI/backend/app/engines/energy_balance.py))
* `calculate_feeder_balance(db, feeder_id, window_minutes=15) -> EnergyBalanceResult`
  * **Parameters:** `db` (Session): Active database session; `feeder_id` (str): Unique feeder identifier (e.g. `"FEEDER-01"`); `window_minutes` (int): Sliding time window.
  * **Working:** Queries aggregated feeder power, sums downstream consumer readings, deducts $5\%$ technical line loss, computes unaccounted power deficit ($\Delta P$), calculates percentage loss ($0–100\%$), and returns an `EnergyBalanceResult` dataclass.
* `compute_balance(feeder_power, consumer_powers, technical_loss_pct=0.05) -> EnergyBalanceResult`
  * **Parameters:** `feeder_power` (float): Feeder input in Watts; `consumer_powers` (List[float]): Individual consumer loads in Watts; `technical_loss_pct` (float): Technical loss ratio.
  * **Working:** Pure mathematical function evaluating deficit, clamping negative imbalances, and mapping imbalance ratio to exponential severity: `low` ($>5\%$), `medium` ($>15\%$), `high` ($>30\%$), `critical` ($>50\%$).
* `calculate_consumer_deviations(db, feeder_id, window_minutes=15) -> Dict[str, float]`
  * **Parameters:** `db` (Session), `feeder_id` (str), `window_minutes` (int).
  * **Working:** Calculates individual consumer deviations against their historical moving baseline.

---

#### 🛡️ `DeviceTrustEngine` ([`backend/app/engines/device_trust.py`](file:///c:/Users/HP/KavachAI/backend/app/engines/device_trust.py))
* `calculate_trust_score(db, device_id, topic, raw_payload) -> float`
  * **Parameters:** `db` (Session); `device_id` (str); `topic` (str): MQTT topic string; `raw_payload` (dict): Raw JSON payload.
  * **Working:** Runs the 4-pillar Zero Trust verification:
    1. **Identity Pillar (30 pts):** Checks if device is registered in DB.
    2. **Topic Authorization (25 pts):** Ensures meter publishes strictly to authorized topic pattern (`kavachgrid/meter/{id}`).
    3. **Physical Plausibility (30 pts):** Verifies $P \approx V \times I \times PF$ and ensures $V \in [180, 270\text{V}], f \in [47, 53\text{Hz}]$.
    4. **Temporal Plausibility (15 pts):** Rejects future timestamps ($>120\text{s}$) and excessive message jitter.
    Returns a normalized trust score ($0–100$).
* `verify_physical_plausibility(voltage, current, power, power_factor) -> Tuple[bool, float, str]`
  * **Parameters:** `voltage`, `current`, `power`, `power_factor` (floats).
  * **Working:** Computes theoretical power $P_{theo} = V \cdot I \cdot PF$. Rejects physically impossible payloads ($V > 300\text{V}$, $I < 0$).

---

#### 🧠 `AIAnomalyEngine` ([`backend/app/engines/ai_anomaly.py`](file:///c:/Users/HP/KavachAI/backend/app/engines/ai_anomaly.py))
* `calculate_anomaly_score(db, device_id, window_hours=24) -> Tuple[float, Dict[str, Any]]`
  * **Parameters:** `db` (Session), `device_id` (str), `window_hours` (int).
  * **Working:** Extracts time-series telemetry for `device_id`, scales features using `StandardScaler`, feeds the 6-dimensional input vector into the trained Keras Autoencoder model, computes the Mean Squared Error (MSE) between input and reconstructed output:
    $$\text{MSE} = \frac{1}{D} \sum_{i=1}^{D} (x_i - \hat{x}_i)^2$$
    Normalizes MSE to a $0.0–1.0$ anomaly score with dynamic diurnal thresholding.
* `predict_single(features) -> float`
  * **Parameters:** `features` (np.ndarray): 1D array of $[V, I, P, PF, \text{Hour}, \text{DayOfWeek}]$.
  * **Working:** Fast inference returning raw reconstruction error.

---

#### 🏥 `MeterHealthEngine` ([`backend/app/engines/meter_health.py`](file:///c:/Users/HP/KavachAI/backend/app/engines/meter_health.py))
* `calculate_health_score(db, device_id, window_hours=24) -> Tuple[float, Dict[str, Any]]`
  * **Parameters:** `db` (Session), `device_id` (str), `window_hours` (int).
  * **Working:** Evaluates 5 hardware diagnostic metrics:
    1. **Data Completeness (25 pts):** Ratio of received vs expected packets.
    2. **Sensor Variance (25 pts):** Detects frozen/stuck readings ($\sigma^2 < 0.001$).
    3. **Value Plausibility (20 pts):** Absence of impossible voltage/current readings.
    4. **Communication Stability (15 pts):** Interval variance between consecutive packets.
    5. **Calibration Drift (15 pts):** Long-term baseline drift away from nominal grid frequency/voltage.
    Returns composite health ($0–100$) and generates maintenance tickets when health $< 50$.

---

#### ⚖️ `RiskEngine` ([`backend/app/engines/risk_engine.py`](file:///c:/Users/HP/KavachAI/backend/app/engines/risk_engine.py))
* `calculate_device_risk(db, device_id, window_hours=24) -> RiskScoreResult`
  * **Parameters:** `db` (Session), `device_id` (str), `window_hours` (int).
  * **Working:** Fetches output from all sub-engines and computes the weighted composite score:
    $$\text{Risk} = 0.30(E) + 0.25(A) + 0.20(100 - H) + 0.15(100 - T) + 0.10(100 - C)$$
    Classifies risk into tiers: `low` ($<30$), `medium` ($30–60$), `high` ($60–80$), `critical` ($>80$), and generates human-readable forensic explanations.
* `rank_all_devices(db, zone_id=None) -> List[RiskScoreResult]`
  * **Parameters:** `db` (Session), `zone_id` (Optional[str]).
  * **Working:** Recalculates risk for all active meters in a zone and sorts descending by risk score to generate the control room suspect leaderboard.

---

#### 📍 `LocalizationEngine` ([`backend/app/engines/localization.py`](file:///c:/Users/HP/KavachAI/backend/app/engines/localization.py))
* `localize_zone(db, zone_id="ZONE-A") -> LocalizationResultData`
  * **Parameters:** `db` (Session), `zone_id` (str).
  * **Working:** Gathers branch CT monitor readings, cross-references consumer risk rankings, computes localization confidence score ($0–100\%$), ranks suspect devices, and assigns action tiers (`Immediate Field Inspection`, `Enhanced Monitoring`, `Routine Audit`).

---

### 4.2. MQTT Ingestion & Message Routing

* `route_and_process_message(topic, payload_raw, db=None) -> Dict[str, Any]` ([`handlers.py`](file:///c:/Users/HP/KavachAI/backend/app/mqtt/handlers.py))
  * **Parameters:** `topic` (str): MQTT topic; `payload_raw` (bytes/str/dict); `db` (Optional Session).
  * **Working:** Validates topic against `validate_topic()`, decodes JSON safely, and dispatches to `handle_feeder_telemetry()`, `handle_consumer_telemetry()`, or `handle_localization_telemetry()`.
* `validate_topic(topic) -> TopicMatchResult` ([`topics.py`](file:///c:/Users/HP/KavachAI/backend/app/mqtt/topics.py))
  * **Working:** Regex pattern matching determining node type (`feeder`, `consumer`, `localization`, `alert`, `command`) and extracting device/zone IDs.

---

### 4.3. FastAPI REST Endpoints & WebSocket

| Route Method & Path | Handler Function | Purpose |
|---|---|---|
| `POST /api/v1/auth/login` | `login_for_access_token()` | Authenticates utility operator and returns JWT Bearer Token |
| `GET /api/v1/devices` | `list_devices()` | Returns all registered feeder and consumer smart meters |
| `POST /api/v1/telemetry` | `ingest_telemetry_http()` | Direct HTTP ingestion endpoint for telemetry |
| `GET /api/v1/telemetry/{device_id}` | `get_device_telemetry()` | Paginated time-series telemetry for a specific meter |
| `GET /api/v1/alerts` | `list_alerts()` | Retrieves active, unacknowledged grid alarms |
| `PUT /api/v1/alerts/{id}/acknowledge` | `acknowledge_alert()` | Marks an alert as acknowledged by an operator |
| `GET /api/v1/risk/ranking` | `get_risk_ranking()` | Returns ranked suspect leaderboard sorted by risk score |
| `GET /api/v1/localization` | `get_localization()` | Returns active zone localization investigations |
| `WS /ws/dashboard` | `websocket_endpoint()` | Real-time WebSocket connection broadcasting live telemetry, alerts, and risk updates |

---

### 4.4. Virtual Grid Simulator Classes

* `VirtualFeeder` ([`simulator/virtual_feeder.py`](file:///c:/Users/HP/KavachAI/simulator/virtual_feeder.py)):
  * `update_consumer_loads(loads: Dict[str, float])`: Aggregates true physical power drawn by all connected houses.
  * `set_theft_tapping(watts: float)`: Injects unmetered theft draw directly onto the transformer feeder.
  * `generate_reading() -> Dict`: Produces realistic feeder telemetry with $\pm 2\text{V}$ voltage jitter and $5\%$ technical line loss.
* `VirtualConsumer` ([`simulator/virtual_consumer.py`](file:///c:/Users/HP/KavachAI/simulator/virtual_consumer.py)):
  * `set_mode(mode, bypass_pct=0.55, spike_multiplier=2.5)`: Configures behavior (`normal`, `theft_bypass`, `stuck_sensor`, `offline`, `power_spike`).
  * `generate_reading() -> Optional[Dict]`: Generates realistic appliance-driven household power profiles.
* `ScenarioEngine` ([`simulator/scenario_engine.py`](file:///c:/Users/HP/KavachAI/simulator/scenario_engine.py)):
  * `run_scenario(scenario_key, duration=120, interval=5) -> Dict`: Synchronizes feeder and consumers in a real-time publish loop.

---

### 4.5. Embedded C++ Firmware Functions

* `void setup()`: Initializes Serial, I2C bus (`Wire.begin()`), INA226/INA219 sensor calibration, and WiFi network connection.
* `void loop()`: Maintains MQTT client connection, samples voltage/current every 5 seconds, computes cumulative energy ($Wh$), serializes JSON with ArduinoJson, and publishes to `kavachgrid/feeder` or `kavachgrid/meter/{id}`.
* `void reconnectMQTT()`: Implements non-blocking auto-reconnect with exponential backoff if the broker connection drops.

---

## 🎬 5. The 6 SIH Demo Scenarios

You can execute any of these 6 demo scenarios during the SIH evaluation:

```powershell
# Interactive Selection Menu
python scripts/simulate_telemetry.py
```

| # | Scenario Key | Name & Description | Observable System Behavior |
|:---:|---|---|---|
| **1** | `normal` | **Normal Operation**<br>All 4 meters report honestly. | • Grid balanced within $5\%$ line loss.<br>• Composite Risk $< 15$ (Green).<br>• Zero alerts generated. |
| **2** | `theft` | **Electricity Theft (H2 Bypass)**<br>Consumer H2 engages a 55% meter bypass. | • Feeder detects $1.3\text{ kW}$ unaccounted deficit ($48.4\%$).<br>• AI Autoencoder MSE spikes to $0.88$.<br>• **H2 Risk jumps to 86/100 (Critical)** $\rightarrow$ Ranked **Suspect #1**. |
| **3** | `meter_failure` | **Meter Sensor Failure (H3)**<br>Sensor freezes due to hardware corrosion. | • Sensor variance drops to $0.000$.<br>• Health Score drops to $40/100$.<br>• **Maintenance Ticket generated** (Zero false accusation of theft). |
| **4** | `comm_drop` | **Communication Outage (H4)**<br>Cellular / WiFi link drops on H4. | • H4 stops transmitting packets.<br>• Status turns `OFFLINE` on Devices page. |
| **5** | `power_spike` | **Abnormal Consumption (H1)**<br>H1 draws $2.5\times$ sanctioned load. | • AI flags load anomaly on timeline.<br>• Energy balance stays 0 because power is reported honestly. |
| **6** | `localization` | **Progressive Localization (Zone A)**<br>Full investigation workflow. | • Localization console narrows candidates in `ZONE-A`.<br>• Generates **"Immediate Field Inspection"** order for Linemen. |

---

## 🚀 6. Quickstart & 1-Click Execution

### Prerequisites
* Python 3.10+ installed
* Node.js 18+ installed

### 1-Click Launch (Starts Backend + Frontend together):
```powershell
# From the root directory:
python start.py
```
*(Or double-click `start.bat` on Windows)*

* **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
* **Backend REST API:** [http://localhost:8000](http://localhost:8000)
* **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **WebSocket Stream:** `ws://localhost:8000/ws/dashboard`

---

## 🧪 7. Testing & Verification

Run the comprehensive unit test suite covering all analytics engines:

```powershell
# From backend directory:
cd backend
python -m pytest tests/test_engines/ -v
```

**Result:** `60 passed in 2.13s (100% test passing)` ✅

---

## 👥 Team & Roles
* **Yash Sharma (Team Lead / AI + Backend):** Architecture, Energy Balance, Meter Health, Composite Risk Engine, Localization, System Integration.
* **Lavlesh:** Database Architecture (PostgreSQL, SQLAlchemy 2.0 ORM, Alembic), Zero Trust Engine, REST APIs.
* **Nitin Rajak:** Frontend Engineering (Next.js 14, Overview, Devices, Risk Monitoring UI, Recharts).
* **Adya:** Frontend Engineering (Localization Console, WebSockets, API Hooks, Animations).
* **Abhishek Shrivastava:** AI/ML Engineer (TensorFlow/Keras Autoencoder Anomaly Model & Dataset Pipeline).
* **Harsh Parmar:** Embedded Hardware & Firmware (ESP32, INA226/INA219 Drivers, MQTT TLS Broker).
