// ============================================
// KAVACHGRID 3.0 — Consumer Node Configuration
// Phase 4: Complete implementation
// ============================================
#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
#define WIFI_SSID       "KavachGrid_Network"
#define WIFI_PASSWORD   "change_me"

// MQTT Configuration
#define MQTT_BROKER     "192.168.1.100"
#define MQTT_PORT       1883
#define MQTT_USERNAME   "consumer_node"
#define MQTT_PASSWORD   "change_me"

// Device Configuration — CHANGE PER NODE
#define MQTT_CLIENT_ID  "kavach-consumer-h1"
#define MQTT_TOPIC      "kavachgrid/meter/h1"
#define DEVICE_ID       "CONSUMER-H1"
#define DEVICE_TYPE     "consumer"

#define PUBLISH_INTERVAL_MS  5000

// Sensor Configuration (INA219)
#define INA_ADDRESS     0x40
#define SHUNT_RESISTOR  0.1  // Ohms

// Edge Analytics Thresholds (Phase 13)
#define VOLTAGE_MIN     200.0
#define VOLTAGE_MAX     260.0
#define CURRENT_MAX     15.0
#define POWER_MAX       3500.0

#endif // CONFIG_H
