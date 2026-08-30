# 🔌 KavachGrid — REST API & WebSocket Reference

Base URL: `http://localhost:8000/api/v1`  
WebSocket URL: `ws://localhost:8000/ws/dashboard`  
Interactive Swagger UI: `http://localhost:8000/docs`

---

## 1. Authentication Endpoints (`/auth`)

### `POST /auth/login`
Authenticates a utility operator and returns a JWT Bearer access token.
* **Request Body:** Form URL-encoded (`username`, `password`)
* **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "u1",
      "username": "operator_admin",
      "role": "admin"
    }
  }
  ```

---

## 2. Device Management (`/devices`)

### `GET /devices`
Returns all registered smart meters (feeder, consumer, localization).
* **Response (200 OK):**
  ```json
  [
    {
      "id": "d1",
      "device_id": "FEEDER-01",
      "device_type": "feeder",
      "name": "Substation Feeder Transformer 1",
      "location": "Sector 4 Substation",
      "status": "online",
      "zone_id": "ZONE-ALL"
    }
  ]
  ```

### `GET /devices/{device_id}`
Returns details for a specific smart meter.

---

## 3. Telemetry Ingestion & History (`/telemetry`)

### `POST /telemetry`
Ingests a single telemetry packet over HTTP.
* **Request Body:**
  ```json
  {
    "device_id": "CONSUMER-H1",
    "voltage": 230.5,
    "current": 2.35,
    "power": 541.6,
    "energy": 1250.8,
    "power_factor": 0.98,
    "frequency": 50.02,
    "timestamp": "2026-08-30T16:00:00Z"
  }
  ```

### `GET /telemetry/{device_id}`
Returns paginated time-series telemetry records for a specific meter.
* **Query Parameters:** `page` (int), `page_size` (int), `start_time` (iso), `end_time` (iso).

---

## 4. Alert Management (`/alerts`)

### `GET /alerts`
Returns active, unacknowledged grid alerts.
* **Response (200 OK):**
  ```json
  [
    {
      "id": "a1",
      "device_id": "CONSUMER-H2",
      "alert_type": "energy_imbalance",
      "severity": "critical",
      "title": "Severe Feeder Energy Deficit (48.4%)",
      "message": "Unaccounted energy deficit detected in Zone A.",
      "acknowledged": false,
      "created_at": "2026-08-30T16:10:00Z"
    }
  ]
  ```

### `PUT /alerts/{alert_id}/acknowledge`
Marks an alert as acknowledged by a control room operator.

---

## 5. Composite Risk Scores (`/risk`)

### `GET /risk/ranking`
Returns the ranked suspect leaderboard sorted descending by composite risk score.
* **Response (200 OK):**
  ```json
  {
    "rankings": [
      {
        "device_id": "CONSUMER-H2",
        "overall_score": 86.4,
        "energy_balance_score": 92.0,
        "ai_anomaly_score": 88.0,
        "meter_health_score": 95.0,
        "device_trust_score": 100.0,
        "comm_reliability_score": 98.0,
        "risk_level": "critical",
        "details": {
          "suspect_reason": "48.4% energy deficit + high AI anomaly score"
        }
      }
    ]
  }
  ```

---

## 6. Progressive Localization (`/localization`)

### `GET /localization`
Returns active zone localization investigations with suspect candidate breakdowns and action recommendations.

---

## 7. Real-Time WebSocket (`/ws/dashboard`)
* Connects via `ws://localhost:8000/ws/dashboard`.
* Pushes real-time JSON events to connected dashboards:
  * `telemetry_update`: Broadcasts new incoming voltage/current/power packets.
  * `alert_created`: Broadcasts newly generated system alarms.
  * `risk_updated`: Pushes newly computed risk scores.
  * `device_status`: Broadcasts online/offline/warning transitions.
