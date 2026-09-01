/*
 * ============================================================
 *  KAVACHGRID 3.0 — Consumer Node Firmware (House 1)
 *  Board: ESP32 Dev Module
 *  Sensors:
 *    - ACS712 Current Sensor -> GPIO 34
 *
 *  MQTT Topics:
 *    - Telemetry: kavachgrid/meter/CONSUMER-01
 *    - Alerts:    kavachgrid/alerts/CONSUMER-01
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
  const int CURRENT_PIN = 34;    // ESP32 ADC Pin
  const int ADC_RESOLUTION = 4095;
  const float ADC_REF_VOLTAGE = 3.3;
#endif

// Calibration Constants
const float ACS712_SENSITIVITY = 0.185;  // V/A for ACS712-5A (use 0.066 for 30A, 0.100 for 20A)
const float NOMINAL_VOLTAGE    = 230.0;  // AC supply estimation voltage

// Anomaly thresholds
const float OVERCURRENT_THRESHOLD  = 5.0;    // Amps
const float ZERO_CURRENT_THRESHOLD = 0.01;
const int   ZERO_CURRENT_COUNT_MAX = 12;

// Timing & Sampling
const unsigned long TELEMETRY_INTERVAL_MS = 5000;
const unsigned long WIFI_RETRY_DELAY_MS   = 5000;
const unsigned long MQTT_RETRY_DELAY_MS   = 3000;
const int NUM_SAMPLES = 20;

// Globals
WiFiClient espClient;
PubSubClient mqtt(espClient);

float zeroCurrentVoltage = 2.5; // Auto-calibrated in setup()

// Forward declarations
void connectWiFi();
void connectMQTT();
void publishTelemetry();
void checkAnomalies(float current, float power);
void calibrateACS712();
float readCurrent();
float round2(float value);

unsigned long lastTelemetryMs  = 0;
unsigned long sequenceNum      = 0;
unsigned long bootTimeMs       = 0;
int           zeroCurrentCount = 0;

// ===================== SETUP =====================
void setup() {
  Serial.begin(115200);
  delay(500);

#if defined(ESP32)
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
#endif

  Serial.println();
  Serial.println("============================================");
  Serial.println("  KAVACHGRID 3.0 — Consumer Node (House 1)");
  Serial.println("  Device: " + String(DEVICE_ID));
  Serial.println("============================================");

  calibrateACS712();

  connectWiFi();
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setBufferSize(512);
  connectMQTT();

  bootTimeMs = millis();
  Serial.println("[OK] Consumer node (House 1) ready.");
}

// ===================== CALIBRATION =====================
void calibrateACS712() {
  Serial.print("[CAL] Calibrating ACS712 zero-current baseline...");
  long sum = 0;
  for (int i = 0; i < 60; i++) {
    sum += analogRead(CURRENT_PIN);
    delay(10);
  }
  float avgRaw = (float)sum / 60.0;
  zeroCurrentVoltage = (avgRaw / (float)ADC_RESOLUTION) * ADC_REF_VOLTAGE;
  Serial.print(" Done! Zero baseline = ");
  Serial.print(zeroCurrentVoltage, 3);
  Serial.println(" V");
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
float readCurrent() {
  long sum = 0;
  for (int i = 0; i < NUM_SAMPLES; i++) {
    sum += analogRead(CURRENT_PIN);
    delayMicroseconds(200);
  }
  float avgRaw = (float)sum / NUM_SAMPLES;
  float voltage = (avgRaw / (float)ADC_RESOLUTION) * ADC_REF_VOLTAGE;
  float current = (voltage - zeroCurrentVoltage) / ACS712_SENSITIVITY;
  
  // Clean small ADC noise floor
  if (abs(current) < 0.08) {
    current = 0.0;
  }
  return abs(current);
}

// ===================== TELEMETRY =====================
void publishTelemetry() {
  float current_A = readCurrent();
  float power_W   = current_A * NOMINAL_VOLTAGE;

  sequenceNum++;
  float uptimeSec = (millis() - bootTimeMs) / 1000.0;

  float freq = 49.95 + ((float)random(0, 15) / 100.0);
  float pf   = 0.98;

  char buffer[384];
  snprintf(buffer, sizeof(buffer),
    "{\"device_id\":\"%s\",\"voltage\":%.1f,\"current\":%.2f,\"power\":%.2f,\"frequency\":%.2f,\"power_factor\":%.2f,\"uptime\":%lu,\"seq\":%lu,\"rssi\":%d}",
    DEVICE_ID, NOMINAL_VOLTAGE, current_A, power_W, freq, pf, (unsigned long)uptimeSec, sequenceNum, (int)WiFi.RSSI()
  );

  if (mqtt.publish(MQTT_TOPIC, buffer)) {
    Serial.print("[TX] ");
    Serial.println(buffer);
  } else {
    Serial.println("[ERR] MQTT publish failed");
  }

  checkAnomalies(current_A, power_W);
}

// ===================== EDGE ANOMALY DETECTION =====================
void checkAnomalies(float current, float power) {
  bool anomaly = false;
  String alertType = "";
  String details = "";

  if (current > OVERCURRENT_THRESHOLD) {
    anomaly = true;
    alertType = "OVERCURRENT";
    details = "Current " + String(current, 2) + "A exceeds " + String(OVERCURRENT_THRESHOLD) + "A";
    zeroCurrentCount = 0;
  } else if (current < ZERO_CURRENT_THRESHOLD) {
    zeroCurrentCount++;
    if (zeroCurrentCount >= ZERO_CURRENT_COUNT_MAX) {
      anomaly = true;
      alertType = "ZERO_CONSUMPTION";
      details = "Zero current for " + String(zeroCurrentCount * 5) + "s — possible meter bypass";
      zeroCurrentCount = 0;
    }
  } else {
    zeroCurrentCount = 0;
  }

  if (anomaly) {
    char alertBuf[256];
    snprintf(alertBuf, sizeof(alertBuf),
      "{\"device_id\":\"%s\",\"alert_type\":\"%s\",\"severity\":\"%s\",\"details\":\"%s\",\"current\":%.2f,\"power\":%.2f}",
      DEVICE_ID, alertType.c_str(), (alertType == "OVERCURRENT" ? "high" : "medium"), details.c_str(), current, power
    );
    mqtt.publish(ALERT_TOPIC, alertBuf);

    Serial.print("[ALERT] ");
    Serial.println(alertBuf);
  }
}

// ===================== CONNECTIVITY =====================
void connectWiFi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.persistent(false);
  WiFi.disconnect(true);
  delay(200);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" OK!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(" FAILED! Restarting...");
    delay(WIFI_RETRY_DELAY_MS);
    ESP.restart();
  }
}

void connectMQTT() {
  int retries = 0;
  while (!mqtt.connected() && retries < 5) {
    Serial.print("[MQTT] Connecting to ");
    Serial.print(MQTT_SERVER);
    Serial.print("...");

    if (mqtt.connect(DEVICE_ID)) {
      Serial.println(" OK!");
      String cmdTopic = "kavachgrid/commands/" + String(DEVICE_ID);
      mqtt.subscribe(cmdTopic.c_str());
      Serial.print("[MQTT] Subscribed to: ");
      Serial.println(cmdTopic);
    } else {
      Serial.print(" FAILED (rc=");
      Serial.print(mqtt.state());
      Serial.println(")");
      retries++;
      delay(MQTT_RETRY_DELAY_MS);
    }
  }
}

// ===================== UTILITIES =====================
float round2(float value) {
  return ((int)(value * 100 + 0.5)) / 100.0;
}
