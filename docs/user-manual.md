# 📖 KavachGrid — Control Room User Manual

---

## 1. Overview Dashboard (`/`)
* **KPI Cards:** Top banner displays **Grid Unaccounted Loss (%)**, **Active System Alarms**, **Nodes Ingest Status**, and **Active Loss Power (kW)**.
* **Energy Balance Chart:** Compares real-time Substation Feeder Input (Blue) against Total Legitimate Consumer Draw (Purple) and Active Theft Deficit (Red).
* **Alerts Feed:** Live streaming warnings with 1-click **Acknowledge** action.

---

## 2. Smart Meter Devices View (`/devices`)
* **Fleet Table:** Lists all Feeder and Household meters with real-time health bars (0–100%).
* **Search & Filters:** Filter by Zone (`ZONE-A`), Status (`ONLINE`, `WARNING`, `OFFLINE`), or Device ID.
* **Device Modal:** Click any device card to view real-time voltage, current, and last-seen timestamps.

---

## 3. Risk Monitoring & Leaderboard (`/risk`)
* **Suspect Leaderboard:** Ranks all consumers by their composite 5-pillar risk score.
* **Risk Gauge:** Dynamic speedometer dial visualizing risk tier:
  * `0–30`: Normal (Green)
  * `30–60`: Moderate (Blue)
  * `60–80`: High (Orange)
  * `80–100`: Critical (Red)
* **AI Anomaly Timeline:** Line chart tracking Neural Autoencoder reconstruction MSE error spikes.

---

## 4. Progressive Localization Console (`/localization`)
* **Active Zone Investigations:** Displays priority level (`CRITICAL`, `HIGH`, `MEDIUM`) and candidate narrowing confidence ($0–100\%$).
* **Suspect Dossier Cards:** Displays specific suspect reasoning (e.g., *"48.4% energy deficit + AI anomaly"*) and recommended field action (*"Immediate Field Inspection"*).
* **Investigation Modal:** Allows control room engineers to update investigation status (`pending` $\rightarrow$ `investigating` $\rightarrow$ `resolved`) and enter field lineman notes.
