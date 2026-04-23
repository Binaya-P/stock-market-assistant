# Project Timeline — NepseAI

## Phase 0 — Initial Setup
- Created project structure
- Set up virtual environment
- Initialized Git repository
- Created docs folder

---

## Phase 1 — Basic Signal System
- Built initial signal logic
- Used:
  - volume
  - large_trade_ratio
- Output:
  - BUY / WATCH

Issue:
- Illiquid stocks ranked high
- Over-reliance on large trades

---

## Phase 2 — Signal Engine v2 (Major Upgrade)

### Changes:
- Added:
  - trades (activity)
  - normalization
- Introduced:
  - confidence score
  - activity score

### Problem discovered:
- Garbage stocks (low trades, high large trades) dominating

---

## Phase 3 — Liquidity Fix (Critical Turning Point)

### Fix applied:
- Added filters:
  - volume > 50,000
  - trades > 200

### Adjusted weights:
- large_trade_ratio reduced
- activity increased importance

### Result:
- Real stocks like NHPC started ranking
- Illiquid stocks removed

---

## Phase 4 — Signal Redesign

### Removed:
- BUY signal

### Introduced:
- ACCUMULATION
- WATCH
- IGNORE

Reason:
- Separate signal generation from decision making

---

## Phase 5 — Threshold Problem

Issue:
- All signals became IGNORE

Fix:
- Lowered thresholds:
  - 45 → ACCUMULATION
  - 35 → WATCH

---

## Phase 6 — Hybrid Strategy Planning

Decisions made:

- Capital split strategy
- Confidence-based allocation
- Risk-based exits

Rules:
- 25% cash reserve
- max 20% per stock
- dynamic position sizing

---

## Phase 7 — Portfolio Tracking

Created:
- portfolio_manager
- state/portfolio.csv

Added initial trades:
- JHAPA (10 units @ 1482.83)
- MABEL (15 units @ 684.62)

---

## Phase 8 — Decision Engine

Created:
- process_signals()

Logic:
- New stock → BUY candidate
- Existing stock:
  - confidence ↑ → upgrade
  - confidence ↓ → exit

---

## Phase 9 — Data Issues Discovered

Problem:
- No cleaned data pipeline
- raw/ and cleaned/ confusion
- "No objects to concatenate" error

Decision:
- Skip raw → directly store usable data
- Move toward summary-based system

---

## Phase 10 — Collector Issues

Problem:
- Data not saving

Cause:
- missing folder (data/raw)

Fix:
- ensure directory creation

---

## Phase 11 — System Stabilization

Current state:

✔ Signal engine working  
✔ Liquidity filtering working  
✔ Portfolio system initialized  
✔ Decision engine basic version working  

---

## Current Output Example

- NHPC → ACCUMULATION
- HFIN → WATCH
- SOHL → WATCH

---

## Next Phases (Planned)

### Phase 12
- Data pipeline completion
- summary/ structure

### Phase 13
- Market mode detection (bull/bear)

### Phase 14
- Automated execution logic

### Phase 15
- Backtesting system

### Phase 16
- Performance tracking (daily/weekly/monthly/yearly)

---

## Key Lessons Learned

- Raw signals ≠ tradable signals
- Liquidity is critical
- Thresholds must match scoring system
- Separate:
  - signal generation
  - decision making
  - execution

---

## Philosophy

"Detect opportunity → evaluate risk → allocate capital"

NOT

"Blindly follow signals"