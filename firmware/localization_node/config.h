// ============================================
// KAVACHGRID 3.0 — Localization Node Configuration
// Optional — for progressive localization demo
// ============================================
#ifndef CONFIG_H
#define CONFIG_H

#define WIFI_SSID       "KavachGrid_Network"
#define WIFI_PASSWORD   "change_me"

#define MQTT_BROKER     "192.168.1.100"
#define MQTT_PORT       1883
#define MQTT_USERNAME   "localization_node"
#define MQTT_PASSWORD   "change_me"
#define MQTT_CLIENT_ID  "kavach-loc-01"
#define MQTT_TOPIC      "kavachgrid/localization/zone1"

#define DEVICE_ID       "LOC-ZONE1"
#define DEVICE_TYPE     "localization"
#define PUBLISH_INTERVAL_MS  5000

// Current Clamp Sensor Configuration
#define CT_PIN          34   // ADC pin for current clamp
#define CT_RATIO        100  // Current transformer ratio
#define BURDEN_RESISTOR 33.0 // Burden resistor in Ohms

#endif // CONFIG_H
