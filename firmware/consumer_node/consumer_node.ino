#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "mqtt.kavachgrid.local"; // Replace with your computer's IP address

WiFiClient espClient;
PubSubClient client(espClient);

// ESP-12E has one analog pin
const int currentPin = A0; 

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  client.setServer(mqtt_server, 1883);
}

void loop() {
  // Use "CONSUMER-01" for House 1, and "CONSUMER-02" for House 2
  if (!client.connected()) { client.connect("CONSUMER-01"); } 
  client.loop();

  int currentRaw = analogRead(currentPin);
  
  // Note: Calibration multiplier (adjust this!)
  float current_A = (currentRaw - 512) * 0.074; 
  float power_W = current_A * 9.0; // Assuming 9V battery

  StaticJsonDocument<256> doc;
  doc["device_id"] = "CONSUMER-01"; // Change to 02 for House 2
  doc["current"] = abs(current_A);
  doc["power"] = abs(power_W);

  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  
  Serial.println(jsonBuffer);
  client.publish("kavachgrid/meter/CONSUMER-01", jsonBuffer); // Change to 02 for House 2
  
  delay(5000);
}
