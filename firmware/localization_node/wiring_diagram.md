# Localization Node (ESP32 + CT Clamp) Wiring Diagram

```mermaid
flowchart TD
    %% Define components
    ESP32(ESP32 NodeMCU)
    CT(CT Clamp e.g. SCT-013-000)
    JACK(3.5mm Audio Jack / Terminal)
    V_DIVIDER(Voltage Divider & Burden Resistor)

    %% Connections
    ESP32_3V3((3V3)) -- 3.3V Power --> V_DIVIDER_R1((R1 10k))
    ESP32_GND((GND)) -- GND --> V_DIVIDER_R2((R2 10k))
    
    %% Midpoint
    V_DIVIDER_R1((R1 10k)) --- MIDPOINT((Midpoint 1.65V))
    V_DIVIDER_R2((R2 10k)) --- MIDPOINT((Midpoint 1.65V))
    
    %% Burden and CT
    MIDPOINT((Midpoint 1.65V)) -- Reference --> JACK_SLEEVE((Jack Sleeve))
    JACK_TIP((Jack Tip)) -- Signal --> ESP32_D34((GPIO 34 / ADC1))
    
    %% Burden Resistor (e.g. 33 ohms for SCT-013-000 100A/50mA)
    JACK_SLEEVE((Jack Sleeve)) -. Burden Resistor (33Ω) .- JACK_TIP((Jack Tip))
    
    %% CT Clamp
    CT(CT Clamp) ==> JACK(3.5mm Audio Jack)
```

### Notes
- The CT Clamp outputs an AC current which needs to be converted to an AC voltage using a Burden Resistor (if the CT doesn't have one built-in).
- A voltage divider (R1 and R2, typically 10kΩ each) creates a DC bias (midpoint) of 1.65V (half of 3.3V) so the AC signal oscillates between 0V and 3.3V, keeping it within the ESP32's ADC range.
- The analog signal is read by an ADC pin on the ESP32 (e.g., GPIO 34).
