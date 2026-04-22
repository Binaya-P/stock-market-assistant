# Data Server (Old Laptop)

## 🎯 Purpose
This device acts as a **data engine** for the system.  
It collects, cleans, aggregates, and stores stock market data from the Nepal Stock Exchange (NEPSE).

It must remain **stable and low-maintenance**.

---

## 🧠 Responsibilities

### 1. Data Collection
- Run once daily after market close (~3:30–4:00 PM)
- Fetch full floorsheet data from NEPSE API
- Save raw data temporarily

---

### 2. Data Cleaning
- Remove duplicates using `contractId`
- Validate and standardize:
  - `stockSymbol`
  - `contractQuantity`
  - `contractRate`
  - `tradeTime`
- Remove invalid or missing rows

---

### 3. Data Storage

#### Folder Structure

data/
├── raw/
├── clean/
│   ├── YYYY-MM-DD.csv
├── weekly/
│   ├── YYYY-Wxx.csv
├── monthly/
│   ├── YYYY-MM.csv
├── yearly/
│   ├── YYYY.csv

---

### 4. Data Retention Policy

- Raw data → delete after **14 days**
- Clean data → keep **permanently**
- Aggregated data → keep **permanently**

---

### 5. Aggregation

#### Daily (after cleaning)
For each stock:
- total volume
- total trades
- average price
- high / low price
- closing price
- price change %

---

#### Weekly
- Combine last 5 trading days

#### Monthly
- Combine all trading days in month

#### Yearly
- Combine all months

---

### 6. Signal Generation (Daily)

- Run signal engine after cleaning
- Output:

reports/
├── YYYY-MM-DD_signals.csv

---

## ⚙️ Execution

- Runs automatically via scheduler (cron / task scheduler)
- No manual interaction required

---

## ❌ What This Device Does NOT Do

- No heavy analysis
- No model training
- No experimentation
- No manual trading decisions

---

## 🧠 Design Philosophy

- Stability > complexity
- Consistency > speed
- Automation > manual control

---

## 🚀 Future Upgrades

- Move from CSV → SQLite
- Add mid-day snapshot collection
- Improve aggregation logic