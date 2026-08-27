# Feeder Node (ESP32 + INA226) Wiring Diagram

```mermaid
flowchart TD
    %% Define components
    ESP32(ESP32 NodeMCU)
    INA226(INA226 Power Sensor)
    PSU(Power Supply / Main Line)
    LOAD(Feeder Load)

    %% Wiring connections
    ESP32_3V3((3V3)) -- VCC --> INA226_VCC((VCC))
    ESP32_GND((GND)) -- GND --> INA226_GND((GND))
    ESP32_D22((GPIO 22 / SCL)) -- I2C SCL --> INA226_SCL((SCL))
    ESP32_D21((GPIO 21 / SDA)) -- I2C SDA --> INA226_SDA((SDA))

    %% Power path
    PSU_V+((V+)) -- Power Line --> INA226_IN+((IN+))
    INA226_IN-((IN-)) -- Power Line --> LOAD_V+((Load +))
    PSU_V-((V- / GND)) -- Power Line --> LOAD_V-((Load -))
    
    %% Voltage sensing (VBUS)
    PSU_V+((V+)) -. VBUS Sensing .-> INA226_VBUS((VBUS))
```

### Notes
- The INA226 communicates via I2C (default pins 21/SDA and 22/SCL on ESP32).
- The `IN+` and `IN-` pins are connected in series with the high side of the load to measure current across the internal shunt resistor.
- The `VBUS` pin is connected to the load's positive supply to measure bus voltage.
