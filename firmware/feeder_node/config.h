// ============================================
// KAVACHGRID 3.0 — Feeder Node Configuration
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
#define MQTT_USERNAME   "feeder_node"
#define MQTT_PASSWORD   "change_me"
#define MQTT_CLIENT_ID  "kavach-feeder-01"
#define MQTT_TOPIC      "kavachgrid/feeder"

// Device Configuration
#define DEVICE_ID       "FEEDER-01"
#define DEVICE_TYPE     "feeder"
#define PUBLISH_INTERVAL_MS  5000

// Sensor Configuration (INA226)
#define INA_ADDRESS     0x40
#define SHUNT_RESISTOR  0.1  // Ohms

// Edge Analytics Thresholds (Phase 13)
#define VOLTAGE_MIN     200.0
#define VOLTAGE_MAX     260.0
#define CURRENT_MAX     30.0
#define POWER_MAX       7000.0

#endif // CONFIG_H
