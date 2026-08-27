# KAVACHGRID 3.0 — Team Task Distribution (Phases 3–16)

> **Phases 1 & 2 are COMPLETE** (Project Structure + Database Design)

---

## User Review Required
Please review this task distribution plan. If the assignments look good, approve this plan so we can proceed with execution (starting with Phase 3).

## 👥 Team Roster

| # | Name | Role | Strength |
|---|------|------|----------|
| 1 | **Lavlesh** | Backend & Database Engineer | Database, Backend (FastAPI, SQLAlchemy) |
| 2 | **Nitin Rajak** | Frontend & Design Engineer | UI/UX Design, Next.js, React |
| 3 | **Adya** | Frontend & Design Engineer | UI/UX Design, Next.js, React |
| 4 | **Abhishek Shrivastava** | AI/ML Engineer | TensorFlow, Keras, Scikit-Learn, Model Training |
| 5 | **Harsh Parmar** | Hardware & Firmware Engineer | ESP32, Arduino, Sensors, Wiring, Embedded C++ |
| 6 | **Yash Sharma** | Team Lead / AI + Backend | AI, Backend, Architecture, Integration, All tasks |

---

## 📊 Phase Overview Map

| Phase | Title | Primary Owner | Support | Effort |
|-------|-------|--------------|---------|--------|
| 3 | MQTT Infrastructure | **Lavlesh** + **Harsh** | Yash | 1 day |
| 4 | ESP32 Firmware | **Harsh** | Yash | 2 days |
| 5 | FastAPI Backend | **Lavlesh** | Yash | 2 days |
| 6 | Energy Balance Engine | **Yash** | Lavlesh | 1 day |
| 7 | Meter Health Engine | **Yash** | Lavlesh | 1 day |
| 8 | AI Anomaly Detection | **Abhishek** + **Yash** | — | 3 days |
| 9 | Device Trust Engine | **Lavlesh** | Yash | 1 day |
| 10 | KAVACH Risk Engine | **Yash** | Abhishek | 1 day |
| 11 | Progressive Localization | **Yash** | Abhishek | 1 day |
| 12 | Dashboard | **Nitin** + **Adya** | Yash | 3 days |
| 13 | Edge Computing | **Harsh** | Yash | 1 day |
| 14 | Testing | **All Team** | — | 2 days |
| 15 | SIH Demo Scenarios | **All Team** | — | 1 day |
| 16 | Documentation | **All Team** | — | 2 days |

---

---

# PHASE 3 — MQTT INFRASTRUCTURE

## 🎯 Objective
Set up the MQTT communication layer that connects ESP32 devices to the FastAPI backend with topic hierarchy, TLS security, authentication, and async message handling.

## 👤 Task Assignment

### Lavlesh (Primary — Backend MQTT Integration)
**Tasks:**
1. Build the async MQTT subscriber client inside FastAPI
2. Implement message handlers that route MQTT messages to the correct service
3. Implement MQTT-to-database ingestion pipeline
4. Write topic validation logic
5. Test MQTT ↔ Backend connectivity

### Harsh (Primary — Broker Configuration & TLS)
**Tasks:**
1. Configure Mosquitto broker for production use
2. Set up TLS certificates using the generation script
3. Configure username/password authentication
4. Set up topic-level ACL (Access Control List)
5. Configure WebSocket listener for dashboard

### Yash (Support — Integration & Review)
**Tasks:**
1. Design the MQTT topic hierarchy
2. Review Lavlesh's MQTT client code and Harsh's broker configuration

---

# PHASE 4 — ESP32 FIRMWARE

## 🎯 Objective
Create complete, production-ready firmware for all 3 node types (Feeder, Consumer, Localization) with sensor reading, JSON generation, MQTT publishing, reconnection logic, error handling, and timestamp support.

## 👤 Task Assignment

### Harsh (Primary — All Firmware)
**Tasks:**
1. Write feeder node firmware (ESP32 + INA226)
2. Write consumer node firmware (ESP32 + INA219)
3. Write localization node firmware (ESP32 + CT Clamp)
4. Implement WiFi/MQTT connection with auto-reconnect
5. Implement JSON payload generation matching the schema
6. Create wiring diagrams for all 3 node types

### Yash (Support — Review & Testing)
**Tasks:**
1. Review all firmware code for correctness
2. Verify JSON payload matches backend schema

---

# PHASE 5 — FASTAPI BACKEND (REST API)

## 🎯 Objective
Build all REST API endpoints with CRUD operations for Devices, Telemetry, Alerts, Risk Scores, and Localization. Implement services layer, authentication, and WebSocket for real-time dashboard updates.

## 👤 Task Assignment

### Lavlesh (Primary — All API Routes & Services)
**Tasks:**
1. Build Services + API routes for Devices, Telemetry, Alerts, Risk, and Localization
2. Build Auth API (login, JWT token generation)
3. Build WebSocket endpoint for real-time dashboard push
4. Implement JWT authentication middleware and API key validation

### Yash (Support — Review, Auth Design, WebSocket)
**Tasks:**
1. Design JWT authentication flow
2. Help with WebSocket implementation
3. Review all API routes and services

---

# PHASE 6 — ENERGY BALANCE ENGINE

## 🎯 Objective
Implement real-time and historical unaccounted energy calculations that detect when more energy enters the feeder than consumers report using.

## 👤 Task Assignment

### Yash (Primary)
**Tasks:**
1. Implement the `EnergyBalanceEngine` class
2. Implement real-time and historical energy balance calculation
3. Implement alert generation when unaccounted energy exceeds threshold
4. Implement energy imbalance score normalization (0-100)

### Lavlesh (Support — DB queries)
**Tasks:**
1. Optimize telemetry queries for energy aggregation

---

# PHASE 7 — METER HEALTH ENGINE

## 🎯 Objective
Detect meter/sensor health issues: missing data, communication failures, sensor drift, stuck readings, and impossible values. Output a Meter Health Score (0-100).

## 👤 Task Assignment

### Yash (Primary)
**Tasks:**
1. Implement the `MeterHealthEngine` class with 5 detection algorithms
2. Implement composite health score calculation (0-100)
3. Implement alert generation for each detection type

### Lavlesh (Support)
**Tasks:**
1. Help with telemetry window queries (last N readings)

---

# PHASE 8 — AI ANOMALY DETECTION ENGINE

## 🎯 Objective
Build an autoencoder-based anomaly detection model that learns normal consumption patterns and flags deviations. Input: Voltage, Current, Power, Time, Day. Output: Anomaly Score (0-1).

## 👤 Task Assignment

### Abhishek (Primary — Model Architecture, Training, Evaluation)
**Tasks:**
1. Design the autoencoder model architecture
2. Implement data preprocessing pipeline and generate synthetic training dataset
3. Implement the training pipeline with early stopping
4. Implement model evaluation (ROC curve, threshold selection)
5. Save trained model

### Yash (Primary — Inference Integration + Review)
**Tasks:**
1. Implement inference module and integrate into FastAPI backend
2. Implement anomaly score calculation

---

# PHASE 9 — DEVICE TRUST ENGINE

## 🎯 Objective
Implement lightweight Zero Trust-inspired validation that verifies device identity, API key, MQTT topic permissions, and payload validity for every incoming message.

## 👤 Task Assignment

### Lavlesh (Primary)
**Tasks:**
1. Implement the `DeviceTrustEngine` class
2. Implement device identity, API key, topic, and payload validity checks
3. Implement trust score calculation (0-100) and integrate into MQTT message handler

### Yash (Support — Review)
**Tasks:**
1. Review trust scoring logic and verify integration

---

# PHASE 10 — KAVACH RISK ENGINE

## 🎯 Objective
Create the composite KAVACH Risk Score (0-100) by combining all 5 engine outputs with weighted scoring. This is the **core intelligence** of KAVACHGRID.

## 👤 Task Assignment

### Yash (Primary)
**Tasks:**
1. Implement the `KavachRiskEngine` class
2. Implement weighted scoring formula and risk level classification
3. Implement periodic scoring cycle (every 30 seconds)
4. Push risk updates via WebSocket

### Abhishek (Support — AI Score Integration)
**Tasks:**
1. Ensure AI anomaly score is properly normalized and integrates correctly

---

# PHASE 11 — PROGRESSIVE LOCALIZATION ENGINE

## 🎯 Objective
Narrow suspicious investigation areas by ranking candidates and calculating localization confidence.

## 👤 Task Assignment

### Yash (Primary)
**Tasks:**
1. Implement the `LocalizationEngine` class
2. Implement zone-level energy balance analysis and suspect ranking algorithm
3. Implement confidence scoring and investigation priority assignment

### Abhishek (Support)
**Tasks:**
1. Review localization algorithm and suggest statistical improvements

---

# PHASE 12 — DASHBOARD

## 🎯 Objective
Build a complete Next.js dashboard with 5 pages: Overview, Devices, Risk Monitoring, Localization, and GIS Map. Uses Material UI, Recharts, and Leaflet.js.

## 👤 Task Assignment

### Nitin (Primary — Overview + Devices + Risk Pages)
**Tasks:**
1. Set up MUI theme provider with KAVACHGRID dark mode branding
2. Build the Sidebar, Header, Overview, Devices, and Risk Monitoring pages
3. Build reusable chart and card components

### Adya (Primary — Localization + GIS Map + Polish)
**Tasks:**
1. Build the Localization and GIS Map pages (with Leaflet.js)
2. Implement API and WebSocket integration hooks
3. Polish all pages (animations, responsive tweaks)

### Yash (Support — API Integration & Review)
**Tasks:**
1. Ensure API endpoints match what Nitin and Adya need
2. Review UI/UX for correctness

---

# PHASE 13 — EDGE COMPUTING

## 🎯 Objective
Implement on-device intelligence on ESP32: basic anomaly threshold detection, communication health monitoring, and local data buffering to reduce bandwidth.

## 👤 Task Assignment

### Harsh (Primary)
**Tasks:**
1. Implement voltage range and current spike detection on ESP32
2. Implement local circular buffer for offline data storage
3. Add edge alert flags to MQTT payload

### Yash (Support)
**Tasks:**
1. Review edge analytics thresholds

---

# PHASE 14 — TESTING

## 🎯 Objective
Create comprehensive test suite covering unit tests, integration tests, API tests, MQTT tests, AI validation tests, and risk engine tests.

## 👤 Task Assignment
Distributed by Component:
- **Lavlesh**: API tests, Service tests, MQTT integration tests
- **Yash**: Engine tests (energy balance, meter health, risk engine, localization)
- **Abhishek**: AI model validation tests
- **Harsh**: Firmware serial output validation, MQTT payload format tests
- **Nitin & Adya**: Dashboard component/integration tests

---

# PHASE 15 — SIH DEMO SCENARIOS

## 🎯 Objective
Build 6 complete demo scenarios that judges can see running live. Each scenario shows a different capability of KAVACHGRID 3.0.

## 👤 Task Assignment
- Scenario 1 (Normal Operation): **Harsh** + **Lavlesh**
- Scenario 2 (Electricity Theft): **Yash** + **Abhishek**
- Scenario 3 (Meter Failure): **Yash**
- Scenario 4 (Communication Failure): **Harsh**
- Scenario 5 (Abnormal Consumption): **Abhishek**
- Scenario 6 (Localization Workflow): **Yash** + **Adya**

---

# PHASE 16 — DOCUMENTATION

## 🎯 Objective
Generate all documentation required for SIH evaluation.

## 👤 Task Assignment
- Architecture Document: **Yash**
- Technical Documentation: **Yash** + **Lavlesh**
- API Documentation: **Lavlesh**
- Database Documentation: **Lavlesh**
- Installation Guide: **Harsh**
- Deployment Guide: **Harsh** + **Yash**
- User Manual: **Nitin** + **Adya**
- Judge Q&A Guide: **Yash**

---

# 📅 Suggested Timeline (Parallel Execution)

```
Week 1 (Days 1-3):
├── Harsh:    Phase 3 (MQTT broker) → Phase 4 (Firmware)
├── Lavlesh:  Phase 3 (MQTT client) → Phase 5 (Backend API)
├── Abhishek: Phase 8 (AI model training — can start independently)
├── Nitin:    Phase 12 (Dashboard — start UI components, mock data)
├── Adya:     Phase 12 (Dashboard — map, localization page)
└── Yash:     Phase 3 (review) → Phase 6 (Energy Balance) → Phase 7 (Meter Health)

Week 2 (Days 4-6):
├── Harsh:    Phase 13 (Edge Computing)
├── Lavlesh:  Phase 9 (Device Trust)
├── Abhishek: Phase 8 (finish) → support Phase 10/11
├── Nitin:    Phase 12 (finish pages, integrate real API)
├── Adya:     Phase 12 (finish, polish, WebSocket)
└── Yash:     Phase 8 (inference) → Phase 10 (Risk Engine) → Phase 11 (Localization)

Week 3 (Days 7-9):
├── All:      Phase 14 (Testing)
├── All:      Phase 15 (Demo Scenarios)
└── All:      Phase 16 (Documentation)
```
