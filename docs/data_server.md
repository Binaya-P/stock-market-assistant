# Data Server / Data Pipeline

## Overview

Handles data collection, storage, and preparation for analysis.

---

## Current Structure

data/
│
├── raw/        # raw NEPSE API data (optional)
├── summary/    # cleaned & usable data (PRIMARY SOURCE)
├── state/      # persistent system state (portfolio)
│   └── portfolio.csv

---

## Data Flow

NEPSE API → Collector → CSV → Analysis Engine

---

## Raw Data Collection

Using nepse API:

- endpoint: floor sheet
- collected manually or via script

Saved as:

data/raw/floor_YYYYMMDD_HHMMSS.csv

---

## Current Decision

Raw data is already mostly clean → we skip heavy cleaning.

👉 System will move toward:
- using **summary/** as main input
- avoiding duplication of raw + cleaned

---

## Summary Data (Planned)

Will contain:

- daily aggregated data
- cleaned + normalized structure

Used directly by signal engine.

---

## State Management

portfolio.csv stores:

- symbol
- quantity
- avg_price (WACC)
- confidence
- last_updated

---

## Missing (To Build)

- Data validation layer
- Deduplication
- Error handling for API failures
- Scheduled collection system

---

## Future Roadmap

### Time-based aggregation:

- Daily summary
- Weekly summary
- Monthly summary
- Yearly summary

### Automation:

- scheduled collector (cron / scheduler)
- auto git sync (optional)

---

## Key Principle

Data integrity first → signals later

(Currently fixing this gap)