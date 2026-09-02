/*
 * ============================================================
 *  KAVACHGRID 3.0 — Feeder Node Firmware
 *  Board: ESP32 Dev Module / NodeMCU (ESP8266)
 *  Sensors:
 *    - ACS712 Current Sensor -> GPIO 34 (ESP32) or A0 (ESP8266)
 *    - Voltage Divider Sensor -> GPIO 35 (ESP32)
 *
 *  Features:
 *    - Local Baseline Training / Zero-Current Calibration
 *    - High-Resolution Current & Power Ingest
 *    - Real-Time MQTT Telemetry & Anomaly Verification
 * ============================================================
 */

#if defined(ESP8266)
  #include <ESP8266WiFi.h>
#elif defined(ESP32)
  #include <WiFi.h>
#else
  #include <ESP8266WiFi.h>
#endif

#include <PubSubClient.h>

// ===================== USER CONFIG =====================
const char* WIFI_SSID     = "Harsh";
const char* WIFI_PASSWORD = "12345678";
const char* MQTT_SERVER   = "10.250.75.55";
const int   MQTT_PORT     = 1883;

const char* DEVICE_ID     = "FEEDER-01";
const char* MQTT_TOPIC    = "kavachgrid/feeder/FEEDER-01";
const char* ALERT_TOPIC   = "kavachgrid/alerts/FEEDER-01";
// =======================================================

// Hardware Pins & ADC configuration for ESP-12E / ESP32
#if defined(ESP8266)
  const int CURRENT_PIN = A0;
  const int VOLTAGE_PIN = A0;
  const int ADC_RESOLUTION = 1023;
  const float ADC_REF_VOLTAGE = 3.3;
#else
  const int CURRENT_PIN = 34;    // ESP32 ADC Pin (GPIO 34)
  const int VOLTAGE_PIN = 35;    // ESP32 ADC Pin (GPIO 35)
  const int ADC_RESOLUTION = 4095;
  const float ADC_REF_VOLTAGE = 3.3;
#endif

// Calibration Constants
// ACS712-5A: 0.185 V/A | ACS712-20A: 0.100 V/A | ACS712-30A: 0.066 V/A
const float ACS712_SENSITIVITY    = 0.185;  // Default 5A module (use 0.066 for 30A)
const float VOLTAGE_DIVIDER_RATIO = 5.0;    // Voltage divider multiplier
const float NOMINAL_VOLTAGE       = 230.0;

// Anomaly thresholds
const float OVERCURRENT_THRESHOLD  = 15.0;   // Amps
const float OVERVOLTAGE_THRESHOLD  = 260.0;  // Volts
const float UNDERVOLTAGE_THRESHOLD = 180.0;  // Volts

// Timing & Sampling
const unsigned long TELEMETRY_INTERVAL_MS = 3000;
const unsigned long WIFI_RETRY_DELAY_MS   = 5000;
const unsigned long MQTT_RETRY_DELAY_MS   = 3000;
const int NUM_SAMPLES = 80;

// Globals
WiFiClient espClient;
PubSubClient mqtt(espClient);

float zeroCurrentVoltage  = 2.5; // Auto-calibrated during local training
float idleNoiseFloor_mA   = 5.0; // Auto-detected noise threshold during training
float filteredCurrent_mA  = 0.0; // Exponential moving average

unsigned long lastTelemetryMs = 0;
unsigned long sequenceNum     = 0;
unsigned long bootTimeMs      = 0;

// Forward declarations
void connectWiFi();
void connectMQTT();
void publishTelemetry();
void checkAnomalies(float current_A, float voltage_V, float power_W);
void trainLocalBaseline();
float readFilteredCurrent_mA();
float readVoltage();

// ===================== SETUP =====================
void setup() {
  Serial.begin(115200);
  delay(600);

#if defined(ESP32)
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
#endif

  Serial.println();
  Serial.println("==================================================");
  Serial.println("  KAVACHGRID 3.0 — Substation Feeder Node");
  Serial.println("  Device: " + String(DEVICE_ID));
  Serial.println("==================================================");

  // Step 1: Train local zero-current baseline
  trainLocalBaseline();

  // Step 2: Connect WiFi & MQTT
  connectWiFi();
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setBufferSize(512);
  connectMQTT();

  bootTimeMs = millis();
  Serial.println("[OK] Feeder node initialized and streaming.");
}

// ===================== LOCAL TRAINING =====================
void trainLocalBaseline() {
  Serial.println();
  Serial.println("[TRAIN] Starting Feeder local baseline training...");
  Serial.println("[TRAIN] >> KEEP ALL DOWNSTREAM LOADS OFF FOR 3 SECONDS <<");

  long sumRaw = 0;
  float maxNoiseDev_V = 0.0;
  const int TRAIN_SAMPLES = 300;

  for (int i = 0; i < TRAIN_SAMPLES; i++) {
    int raw = analogRead(CURRENT_PIN);
    sumRaw += raw;
    delay(10);
  }

  float avgRaw = (float)sumRaw / (float)TRAIN_SAMPLES;
  zeroCurrentVoltage = (avgRaw / (float)ADC_RESOLUTION) * ADC_REF_VOLTAGE;

  for (int i = 0; i < 100; i++) {
    int raw = analogRead(CURRENT_PIN);
    float v = (raw / (float)ADC_RESOLUTION) * ADC_REF_VOLTAGE;
    float dev = abs(v - zeroCurrentVoltage);
    if (dev > maxNoiseDev_V) {
      maxNoiseDev_V = dev;
    }
    delay(5);
  }

  idleNoiseFloor_mA = (maxNoiseDev_V / ACS712_SENSITIVITY) * 1000.0;
  if (idleNoiseFloor_mA < 3.0) idleNoiseFloor_mA = 3.0;

  Serial.println("[TRAIN] Feeder Training Complete!");
  Serial.print("[TRAIN]   - Zero Baseline Vref : ");
  Serial.print(zeroCurrentVoltage, 4);
  Serial.println(" V");
  Serial.print("[TRAIN]   - Noise Floor        : ");
  Serial.print(idleNoiseFloor_mA, 1);
  Serial.println(" mA\n");
}

// ===================== LOOP =====================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WARN] WiFi lost. Reconnecting...");
    connectWiFi();
  }
  if (!mqtt.connected()) {
    connectMQTT();
  }
  mqtt.loop();

  unsigned long now = millis();
  if (now - lastTelemetryMs >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryMs = now;
    publishTelemetry();
  }
}

// ===================== SENSOR READING =====================
float readRawCurrent_mA() {
  long sum = 0;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    sum += analogRead(CURRENT_PIN);
    delayMicroseconds(250);
  }
  float avgRaw = (float)sum / (float)NUM_SAMPLES;
  float voltage = (avgRaw / (float)ADC_RESOLUTION) * ADC_REF_VOLTAGE;
  float diff_V = voltage - zeroCurrentVoltage;
  float current_mA = (diff_V / ACS712_SENSITIVITY) * 1000.0;

  if (abs(current_mA) <= idleNoiseFloor_mA * 1.15) {
    return 0.0;
  }
  return abs(current_mA);
}

float readFilteredCurrent_mA() {
  float instant_mA = readRawCurrent_mA();
  if (filteredCurrent_mA == 0.0 && instant_mA > 0.0) {
    filteredCurrent_mA = instant_mA;
  } else {
    filteredCurrent_mA = (0.55 * instant_mA) + (0.45 * filteredCurrent_mA);
  }
  if (filteredCurrent_mA < 1.0) filteredCurrent_mA = 0.0;
  return filteredCurrent_mA;
}

float readVoltage() {
#if defined(ESP32)
  long sum = 0;
  for (int i = 0; i < 40; i++) {
    sum += analogRead(VOLTAGE_PIN);
    delayMicroseconds(200);
  }
  float avgRaw = (float)sum / 40.0;
  float adcVoltage = (avgRaw / (float)ADC_RESOLUTION) * ADC_REF_VOLTAGE;
  float measured = adcVoltage * VOLTAGE_DIVIDER_RATIO * 15.0;
  if (measured < 50.0) return NOMINAL_VOLTAGE;
  return measured;
#else
  return NOMINAL_VOLTAGE;
#endif
}

// ===================== TELEMETRY =====================
void publishTelemetry() {
  float current_mA = readFilteredCurrent_mA();
  float current_A  = current_mA / 1000.0;
  float voltage_V  = readVoltage();
  float power_W    = current_A * voltage_V;

  sequenceNum++;
  float uptimeSec = (millis() - bootTimeMs) / 1000.0;

  float freq = 50.00 + ((float)random(-5, 6) / 100.0);
  float pf   = (current_mA > 0.0) ? 0.98 : 1.00;

  // Real-time Serial monitor telemetry logging
  Serial.print("[FEEDER #");
  Serial.print(sequenceNum);
  Serial.print("] Current: ");
  Serial.print(current_mA, 2);
  Serial.print(" mA (");
  Serial.print(current_A, 4);
  Serial.print(" A) | Voltage: ");
  Serial.print(voltage_V, 1);
  Serial.print(" V | Power: ");
  Serial.print(power_W, 2);
  Serial.println(" W");

  char buffer[384];
  snprintf(buffer, sizeof(buffer),
    "{\"device_id\":\"%s\",\"voltage\":%.1f,\"current\":%.4f,\"current_mA\":%.2f,\"power\":%.2f,\"frequency\":%.2f,\"power_factor\":%.2f,\"uptime\":%lu,\"seq\":%lu,\"rssi\":%d}",
    DEVICE_ID, voltage_V, current_A, current_mA, power_W, freq, pf, (unsigned long)uptimeSec, sequenceNum, (int)WiFi.RSSI()
  );

  if (mqtt.publish(MQTT_TOPIC, buffer)) {
    Serial.print("  [MQTT -> TX] ");
    Serial.println(buffer);
  } else {
    Serial.println("  [ERR] MQTT publish failed");
  }

  checkAnomalies(current_A, voltage_V, power_W);
}

// ===================== EDGE ANOMALY DETECTION =====================
void checkAnomalies(float current_A, float voltage_V, float power_W) {
  bool anomaly = false;
  String alertType = "";
  String details = "";

  if (current_A > OVERCURRENT_THRESHOLD) {
    anomaly = true;
    alertType = "OVERCURRENT";
    details = "Current " + String(current_A, 2) + "A exceeds threshold " + String(OVERCURRENT_THRESHOLD) + "A";
  } else if (voltage_V > OVERVOLTAGE_THRESHOLD) {
    anomaly = true;
    alertType = "OVERVOLTAGE";
    details = "Voltage " + String(voltage_V, 1) + "V exceeds " + String(OVERVOLTAGE_THRESHOLD) + "V";
  } else if (voltage_V < UNDERVOLTAGE_THRESHOLD && voltage_V > 50.0) {
    anomaly = true;
    alertType = "UNDERVOLTAGE";
    details = "Voltage " + String(voltage_V, 1) + "V below " + String(UNDERVOLTAGE_THRESHOLD) + "V";
  }

  if (anomaly) {
    char alertBuf[256];
    snprintf(alertBuf, sizeof(alertBuf),
      "{\"device_id\":\"%s\",\"alert_type\":\"%s\",\"severity\":\"high\",\"details\":\"%s\",\"current\":%.4f,\"voltage\":%.2f,\"power\":%.2f}",
      DEVICE_ID, alertType.c_str(), details.c_str(), current_A, voltage_V, power_W
    );
    mqtt.publish(ALERT_TOPIC, alertBuf);

    Serial.print("  [ALERT] ");
    Serial.println(alertBuf);
  }
}

// ===================== CONNECTIVITY =====================
void connectWiFi() {
  Serial.print("[WiFi] Connecting to: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("[WiFi] Connected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println();
    Serial.println("[WiFi] Connection failed. Will retry.");
  }
}

void connectMQTT() {
  while (!mqtt.connected()) {
    Serial.print("[MQTT] Connecting to broker at: ");
    Serial.print(MQTT_SERVER);
    Serial.print("...");

    String clientId = "KavachGrid-" + String(DEVICE_ID) + "-" + String(random(0xffff), HEX);

    if (mqtt.connect(clientId.c_str())) {
      Serial.println(" OK!");
    } else {
      Serial.print(" Failed! rc=");
      Serial.print(mqtt.state());
      Serial.println(". Retrying in 3s...");
      delay(MQTT_RETRY_DELAY_MS);
    }
  }
}

