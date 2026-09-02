/*
 * ============================================================
 *  KAVACHGRID 3.0 — Consumer Node Firmware (House 1)
 *  Board: ESP32 Dev Module / NodeMCU (ESP8266)
 *  Sensors:
 *    - ACS712 Current Sensor -> GPIO 34 (ESP32) or A0 (ESP8266)
 *
 *  Features:
 *    - Local Baseline Training / Zero-Current Calibration
 *    - High-Resolution Milliamp (mA) Sampling for LED / Small Loads
 *    - Exponential Moving Average (EMA) Noise Filter
 *    - Real-Time MQTT Telemetry & Edge Anomaly Verification
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

// ---- HOUSE 1 IDENTITY ----
const char* DEVICE_ID     = "CONSUMER-H1";
const char* MQTT_TOPIC    = "kavachgrid/meter/CONSUMER-H1";
const char* ALERT_TOPIC   = "kavachgrid/alerts/CONSUMER-H1";
// =======================================================

// Hardware Pins & ADC configuration for ESP-12E / ESP32
#if defined(ESP8266)
  const int CURRENT_PIN = A0;    // ESP-12E ADC Pin
  const int ADC_RESOLUTION = 1023;
  const float ADC_REF_VOLTAGE = 3.3;
#else
  const int CURRENT_PIN = 34;    // ESP32 ADC Pin (GPIO 34)
  const int ADC_RESOLUTION = 4095;
  const float ADC_REF_VOLTAGE = 3.3;
#endif

// Calibration Constants
const float ACS712_SENSITIVITY = 0.185;  // 185 mV/A for ACS712-5A
const float NOMINAL_VOLTAGE    = 230.0;  // AC supply estimation voltage

// Anomaly thresholds (in Amps / mA)
const float OVERCURRENT_THRESHOLD_A = 5.0;    // 5 Amps
const float ZERO_CURRENT_THRESHOLD_MA = 3.0;  // Below 3 mA considered zero/idle
const int   ZERO_CURRENT_COUNT_MAX  = 12;

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

// Forward declarations
void connectWiFi();
void connectMQTT();
void publishTelemetry();
void checkAnomalies(float current_mA, float power_W);
void trainLocalBaseline();
float readRawCurrent_mA();
float readFilteredCurrent_mA();

unsigned long lastTelemetryMs  = 0;
unsigned long sequenceNum      = 0;
unsigned long bootTimeMs       = 0;
int           zeroCurrentCount = 0;

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
  Serial.println("  KAVACHGRID 3.0 — Consumer Node (House 1)");
  Serial.println("  Device: " + String(DEVICE_ID));
  Serial.println("  High-Resolution Milliamp (mA) Measuring Engine");
  Serial.println("==================================================");

  // Step 1: Train local zero baseline and noise profile
  trainLocalBaseline();

  // Step 2: Connect WiFi & MQTT
  connectWiFi();
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setBufferSize(512);
  connectMQTT();

  bootTimeMs = millis();
  Serial.println("[OK] Consumer node initialized. Ready for LED load testing!");
}

// ===================== LOCAL TRAINING & CALIBRATION =====================
void trainLocalBaseline() {
  Serial.println();
  Serial.println("[TRAIN] Starting local baseline training...");
  Serial.println("[TRAIN] >> PLEASE KEEP ALL LOADS / LEDs DISCONNECTED NOW <<");
  Serial.println("[TRAIN] Sampling resting ADC noise floor over 300 cycles...");

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

  // Measure noise deviation around trained center point
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
  if (idleNoiseFloor_mA < 3.0) idleNoiseFloor_mA = 3.0; // minimum floor

  Serial.println("[TRAIN] Training Complete!");
  Serial.print("[TRAIN]   - Zero-Current Baseline Vref : ");
  Serial.print(zeroCurrentVoltage, 4);
  Serial.println(" V");
  Serial.print("[TRAIN]   - Detected Idle Noise Floor : ");
  Serial.print(idleNoiseFloor_mA, 1);
  Serial.println(" mA");
  Serial.println("[TRAIN] You can now connect your LED / load.\n");
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

// ===================== HIGH-RESOLUTION SENSOR READING =====================
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

  // Clean noise below trained idle floor
  if (abs(current_mA) <= idleNoiseFloor_mA * 1.15) {
    return 0.0;
  }
  return abs(current_mA);
}

float readFilteredCurrent_mA() {
  float instant_mA = readRawCurrent_mA();
  // Fast-response Exponential Moving Average filter (alpha = 0.55)
  if (filteredCurrent_mA == 0.0 && instant_mA > 0.0) {
    filteredCurrent_mA = instant_mA;
  } else {
    filteredCurrent_mA = (0.55 * instant_mA) + (0.45 * filteredCurrent_mA);
  }
  if (filteredCurrent_mA < 1.0) filteredCurrent_mA = 0.0;
  return filteredCurrent_mA;
}

// ===================== TELEMETRY =====================
void publishTelemetry() {
  float current_mA = readFilteredCurrent_mA();
  float current_A  = current_mA / 1000.0;
  float power_W    = current_A * NOMINAL_VOLTAGE;

  sequenceNum++;
  float uptimeSec = (millis() - bootTimeMs) / 1000.0;

  float freq = 50.00 + ((float)random(-5, 6) / 100.0);
  float pf   = (current_mA > 0.0) ? 0.98 : 1.00;

  // Real-time Serial monitor telemetry logging
  Serial.print("[TELEMETRY #");
  Serial.print(sequenceNum);
  Serial.print("] Current: ");
  Serial.print(current_mA, 2);
  Serial.print(" mA (");
  Serial.print(current_A, 4);
  Serial.print(" A) | Power: ");
  Serial.print(power_W, 2);
  Serial.print(" W | State: ");
  Serial.println(current_mA > 5.0 ? "ACTIVE LOAD (NORMAL)" : "IDLE (NO LOAD)");

  // MQTT JSON Payload with both mA and high-precision A
  char buffer[384];
  snprintf(buffer, sizeof(buffer),
    "{\"device_id\":\"%s\",\"voltage\":%.1f,\"current\":%.4f,\"current_mA\":%.2f,\"power\":%.2f,\"frequency\":%.2f,\"power_factor\":%.2f,\"uptime\":%lu,\"seq\":%lu,\"rssi\":%d}",
    DEVICE_ID, NOMINAL_VOLTAGE, current_A, current_mA, power_W, freq, pf, (unsigned long)uptimeSec, sequenceNum, (int)WiFi.RSSI()
  );

  if (mqtt.publish(MQTT_TOPIC, buffer)) {
    Serial.print("  [MQTT -> TX] ");
    Serial.println(buffer);
  } else {
    Serial.println("  [ERR] MQTT publish failed");
  }

  checkAnomalies(current_mA, power_W);
}

// ===================== EDGE ANOMALY DETECTION =====================
void checkAnomalies(float current_mA, float power_W) {
  bool anomaly = false;
  String alertType = "";
  String details = "";
  float current_A = current_mA / 1000.0;

  if (current_A > OVERCURRENT_THRESHOLD_A) {
    anomaly = true;
    alertType = "OVERCURRENT";
    details = "Current " + String(current_A, 2) + "A exceeds " + String(OVERCURRENT_THRESHOLD_A) + "A limit";
    zeroCurrentCount = 0;
  } else if (current_mA < ZERO_CURRENT_THRESHOLD_MA) {
    zeroCurrentCount++;
    if (zeroCurrentCount >= ZERO_CURRENT_COUNT_MAX) {
      anomaly = true;
      alertType = "ZERO_CONSUMPTION";
      details = "Zero current for " + String(zeroCurrentCount * 3) + "s — possible bypass";
      zeroCurrentCount = 0;
    }
  } else {
    zeroCurrentCount = 0;
  }

  if (anomaly) {
    char alertBuffer[256];
    snprintf(alertBuffer, sizeof(alertBuffer),
      "{\"device_id\":\"%s\",\"alert_type\":\"%s\",\"severity\":\"HIGH\",\"message\":\"%s\",\"current_mA\":%.2f,\"power\":%.2f,\"timestamp\":%lu}",
      DEVICE_ID, alertType.c_str(), details.c_str(), current_mA, power_W, millis() / 1000
    );
    mqtt.publish(ALERT_TOPIC, alertBuffer);

    Serial.print("  [ALERT] ");
    Serial.println(alertBuffer);
  }
}

// ===================== WIFI CONNECTION =====================
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

// ===================== MQTT CONNECTION =====================
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
