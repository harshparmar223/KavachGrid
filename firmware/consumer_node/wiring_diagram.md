# Consumer Node (ESP32 + INA219) Wiring Diagram

```mermaid
flowchart TD
    %% Define components
    ESP32(ESP32 NodeMCU)
    INA219(INA219 Power Sensor)
    PSU(Household Supply)
    LOAD(Consumer Load)

    %% Wiring connections
    ESP32_3V3((3V3)) -- VCC --> INA219_VCC((VCC))
    ESP32_GND((GND)) -- GND --> INA219_GND((GND))
    ESP32_D22((GPIO 22 / SCL)) -- I2C SCL --> INA219_SCL((SCL))
    ESP32_D21((GPIO 21 / SDA)) -- I2C SDA --> INA219_SDA((SDA))

    %% Power path
    PSU_V+((V+)) -- Power Line --> INA219_VIN+((VIN+))
    INA219_VIN-((VIN-)) -- Power Line --> LOAD_V+((Load +))
    PSU_V-((V- / GND)) -- Power Line --> LOAD_V-((Load -))
```

### Notes
- The INA219 communicates via I2C (default pins 21/SDA and 22/SCL on ESP32).
- The `VIN+` and `VIN-` pins are connected in series with the high side of the load to measure current across the internal shunt resistor.
- The INA219 measures bus voltage internally from `VIN-` to GND.
