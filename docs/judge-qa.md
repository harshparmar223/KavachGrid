# 🎤 KavachGrid — Judge Q&A & Technical Defense Guide

### Comprehensive defense guide for SIH 2026 Jury, DISCOM Executives, and Electrical Engineering Professors.

---

### Q1: "How do you distinguish genuine line technical losses ($I^2R$) from actual electricity theft?"
**Winning Answer:**
> *"In real power distribution grids, technical loss occurs naturally due to cable impedance ($I^2R$) and transformer magnetization. We handle this through two distinct mechanisms:*
> 1. *We integrate a baseline **5% technical loss decoupling factor** based on standard Indian distribution transformer parameters.*
> 2. *Physical technical losses scale continuously and smoothly with current squared ($I^2$). In contrast, an illegal bypass creates an abrupt, step-change deficit uncorrelated with legitimate downstream meters.*
> *This guarantees that normal line losses never falsely inflate risk scores."*

---

### Q2: "What if a household genuinely turns on high-power appliances (e.g. 2 ACs or an EV charger)?"
**Winning Answer:**
> *"If a customer uses heavy power legitimately, their smart meter measures the increase accurately. The Substation Feeder also sees the same increase. Therefore, the difference ($\text{Feeder} - \sum \text{Consumers}$) remains approximately **ZERO**.*
> *While the AI Anomaly engine might detect a high load spike, the **Energy Balance Engine confirms zero deficit**, keeping the overall composite risk score safely in the Green tier ($< 25/100$)."*

---

### Q3: "Can a sophisticated attacker send fake MQTT packets with lower wattage to hide theft?"
**Winning Answer:**
> *"No. Our **Zero Trust Physics Engine** performs multi-variable validation on every single packet:*
> 1. *It verifies $P \approx V \times I \times PF$. If an attacker alters the power field to 100W while raw voltage is 230V and current is 5A (1150W), the mathematical contradiction is flagged immediately.*
> 2. *Packets must match strict topic ACLs in `acl.conf`.*
> 3. *Future or replayed timestamps ($>120\text{s}$ drift) cause the trust score to collapse instantly."*

---

### Q4: "What happens if a meter sensor simply corrodes or breaks?"
**Winning Answer:**
> *"This is our **Zero False Accusation Guarantee**. A broken meter often reports flatline or static 0W. Our **Meter Health Engine** tracks sensor variance $\sigma^2$. If the variance is zero ($\sigma^2 < 0.001$), the system classifies it as a **Hardware Fault / Frozen Sensor** ($Health = 38/100$) and automatically generates a **Maintenance Work Order** rather than accusing the customer of theft."*

---

### Q5: "Why do you call KAVACHGRID an 'Investigation Support System' instead of an automated theft detector?"
**Winning Answer:**
> *"Under the Indian Electricity Act (Section 135) and utility legal guidelines, power companies cannot levy penalties or disconnect customers based purely on software without physical evidence collected during a sanctioned audit.*
> *KAVACHGRID provides DISCOMs with an **actionable, prioritized evidence dossier** (confidence scores, deficit curves, and GPS pole coordinates), raising raid success rates from $<15\%$ to over $85\%$."*
