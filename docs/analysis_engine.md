# Analysis Engine (Main Laptop)

## 🎯 Purpose
This device is responsible for **analysis, decision-making, and strategy execution**.

It consumes cleaned data from the data server and generates trading insights.

---

## 🧠 Responsibilities

### 1. Data Consumption
- Read from:
  - clean daily data
  - weekly / monthly summaries
  - signal reports

---

### 2. Signal Analysis

Uses:
- volume spikes
- price behavior
- large trade activity
- trend strength

Outputs:
- ranked stocks
- confidence score (%)
- signal type (BUY / WATCH / AVOID)

---

### 3. Strategy Execution (Manual for now)

- Select top candidates (3–5 stocks)
- Allocate capital based on confidence %
- Decide entry timing (mid-day preferred)

---

### 4. Entry Strategy

- 30% → before breakout
- 60% → at breakout
- 10% → after confirmation

---

### 5. Exit Strategy

- -5% → warning
- -8% → reduce position
- -10% → full exit

---

### 6. Profit Strategy

(To be refined)

Options:
- partial profit booking
- signal-based exit
- fixed % targets

---

### 7. Risk Management

- Max 3–5 active positions
- Weighted capital allocation
- Avoid overexposure

---

### 8. Re-entry Logic

- Allowed only if:
  - signal appears again
  - conditions improve

---

## 🧠 Market Assumptions

Based on Nepal Stock Exchange (NEPSE):

- semi-efficient market
- influenced by manipulation
- sector-based movement
- slower trade settlement (T+2)

---

## ⚙️ Workflow

1. Load latest data
2. Run signal engine
3. Rank stocks
4. Apply filters
5. Generate actionable list

---

## 📊 Output Example

stock | confidence | signal
------|------------|--------
ABC   | 78%        | BUY
XYZ   | 74%        | WATCH

---

## ❌ What This Device Does NOT Do

- No data collection
- No raw data storage
- No background scheduling

---

## 🚀 Future Upgrades

- Entry timing engine
- Exit timing optimization
- AI-based pattern detection
- News integration
- Portfolio tracking system