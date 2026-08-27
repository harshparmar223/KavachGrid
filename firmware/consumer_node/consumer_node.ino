#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_INA219.h>

// --- Configuration ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "mqtt.kavachgrid.local";
const int mqtt_port = 1883; // Use 8883 for TLS in production
const char* device_id = "CONSUMER-01";
const char* mqtt_topic = "kavachgrid/meter/CONSUMER-01";

// --- Global Objects ---
WiFiClient espClient;
PubSubClient client(espClient);
Adafruit_INA219 ina219;

// --- State Variables ---
unsigned long lastMsgTime = 0;
const long interval = 5000; // Publish every 5 seconds
float cumulativeEnergy_Wh = 0.0;
unsigned long lastEnergyCalcTime = 0;

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

  // Initialize INA219
  if (!ina219.begin()) {
    Serial.println("Failed to find INA219 chip");
    while (1) { delay(10); }
  }
  Serial.println("INA219 Found!");

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
  
  // Continuous energy integration
  float power_mW = ina219.getPower_mW();
  float power_W = power_mW / 1000.0; 
  float deltaTime_hours = (now - lastEnergyCalcTime) / 3600000.0;
  cumulativeEnergy_Wh += power_W * deltaTime_hours;
  lastEnergyCalcTime = now;

  if (now - lastMsgTime > interval) {
    lastMsgTime = now;

    float voltage_V = ina219.getBusVoltage_V();
    float current_mA = ina219.getCurrent_mA();
    float current_A = current_mA / 1000.0;
    
    float pf = 0.95; 
    float freq = 50.0;

    // Create JSON document
    StaticJsonDocument<256> doc;
    doc["device_id"] = device_id;
    doc["voltage"] = voltage_V;
    doc["current"] = abs(current_A);
    doc["power"] = abs(power_W);
    doc["energy"] = cumulativeEnergy_Wh;
    doc["power_factor"] = pf;
    doc["frequency"] = freq;
    
    // Serialize to string
    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    Serial.print("Publishing message: ");
    Serial.println(jsonBuffer);
    
    client.publish(mqtt_topic, jsonBuffer);
  }
}
