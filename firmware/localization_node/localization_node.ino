#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <EmonLib.h>

// --- Configuration ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "mqtt.kavachgrid.local";
const int mqtt_port = 1883; // Use 8883 for TLS in production
const char* zone_id = "ZONE-A";
const char* device_id = "LOCALIZATION-01";
const char* mqtt_topic = "kavachgrid/localization/ZONE-A";

const int CT_PIN = 34; // ESP32 ADC pin connected to CT clamp circuit

// --- Global Objects ---
WiFiClient espClient;
PubSubClient client(espClient);
EnergyMonitor emon1;

// --- State Variables ---
unsigned long lastMsgTime = 0;
const long interval = 5000; // Publish every 5 seconds
float cumulativeEnergy_Wh = 0.0;
unsigned long lastEnergyCalcTime = 0;
const float REFERENCE_VOLTAGE = 230.0; // Hardcoded reference for API compatibility

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(device_id)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  // Initialize EmonLib
  // Current: input pin, calibration.
  // Calibration value depends on the CT and burden resistor.
  emon1.current(CT_PIN, 111.1); 

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  
  lastEnergyCalcTime = millis();
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  
  // Measure Current
  double Irms = emon1.calcIrms(1480);  // Calculate Irms only
  float power_W = Irms * REFERENCE_VOLTAGE; // Apparent power assumption for schema

  // Continuous energy integration
  float deltaTime_hours = (now - lastEnergyCalcTime) / 3600000.0;
  cumulativeEnergy_Wh += power_W * deltaTime_hours;
  lastEnergyCalcTime = now;

  if (now - lastMsgTime > interval) {
    lastMsgTime = now;

    // Create JSON document (using Telemetry schema for consistency if expected)
    StaticJsonDocument<256> doc;
    doc["device_id"] = device_id;
    doc["voltage"] = REFERENCE_VOLTAGE;
    doc["current"] = Irms;
    doc["power"] = power_W;
    doc["energy"] = cumulativeEnergy_Wh;
    doc["power_factor"] = 0.95;
    doc["frequency"] = 50.0;
    
    // Serialize to string
    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    Serial.print("Publishing message: ");
    Serial.println(jsonBuffer);
    
    client.publish(mqtt_topic, jsonBuffer);
  }
}
