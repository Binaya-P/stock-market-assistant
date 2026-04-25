# Project Timeline - NepseAI

## Phase 0 - Initial Setup
- Created project structure
- Set up virtual environment
- Initialized Git repository
- Created docs folder

---

## Phase 1 - Basic Signal System
- Built initial signal logic
- Used volume and large trade ratio
- Output BUY and WATCH style labels

Issue:
- Illiquid stocks ranked high
- Large trades were overweighted

---

## Phase 2 - Signal Engine v2

Changes:
- Added trade activity
- Added normalization
- Introduced confidence scoring

Problem discovered:
- Low-quality stocks still surfaced too often

---

## Phase 3 - Liquidity Fix

Fix applied:
- Added higher volume and trade-count filters
- Reduced large-trade influence
- Increased activity importance

Result:
- More realistic liquid stocks started surfacing

---

## Phase 4 - Signal Redesign

Changes:
- Removed direct BUY output from the signal layer
- Introduced `ACCUMULATION`, `WATCH`, and `IGNORE`

Reason:
- Keep signal generation separate from decision making

---

## Phase 5 - Threshold Recalibration

Problem:
- Most outputs collapsed into `IGNORE`

Fix:
- Lowered confidence thresholds for `ACCUMULATION` and `WATCH`

---

## Phase 6 - Hybrid Strategy Planning

Decisions made:
- Capital split strategy
- Confidence-based allocation
- Risk-based exits

Rules discussed:
- Keep a cash reserve
- Cap allocation per stock
- Use dynamic sizing later

---

## Phase 7 - Portfolio Tracking

Created:
- `portfolio_manager`
- `data/state/portfolio.csv`

Added tracked positions:
- `JHAPA`
- `MABEL`

Key Rule:
- Portfolio is **user-controlled only**
- System cannot auto-update real holdings

---

## Phase 8 - Decision Engine

Created:
- `process_signals()`

Logic:
- Suggest ADD, HOLD, REDUCE, EXIT
- Separated system decision from execution

---

## Phase 9 - Data Pipeline Reframe

Problem:
- Raw vs processed data responsibilities unclear

Decision:
- Stabilize raw-data layer first
- Build summaries before upgrading signals

---

## Phase 10 - Collector Stabilization

Fixes:
- Ensured raw-data directories exist
- Cleaned collector save behavior
- Removed risky auto-git actions

---

## Phase 11 - Raw Data Model Cleanup

Changes:
- Preserved `tradeTime` from exchange
- Added `collectionTime`
- Added `snapshotId`

Goal:
- Clean audit trail of market data

---

## Phase 12 - Summary Pipeline Foundation

Built:
- Shared summary files
- Daily, weekly, monthly, yearly summaries
- Friday scheduling
- Deduplication via `contractId`

Confirmed runtime:
- Python 3.12

---

## Phase 13 - Summary Validation Iteration

Added:
- Raw dataset reporting
- Snapshot indexing
- Summary health checks
- Validation issue tracking

---

## Phase 14 - SQLite Canonical Store

Created:
- `nepseai.db`

Synced:
- Raw contracts
- Summary tables
- Health + validation reports

---

## Phase 15 - Reconciliation Iteration

Added:
- Duplicate contract tracking
- CSV export of retained vs dropped trades

---

## Phase 16 - Validation & Metadata

Added:
- Stronger validation rules
- SQLite metadata tracking
- Safer schema handling

---

## Phase 17 - Scheduler & Archive

Added:
- Scheduled raw fetch (1:00 PM, 3:30 PM)
- Summary rebuild pipeline
- Archive snapshots
- Restart-safe scheduler

---

## Phase 18 - Decision System Upgrade

Changes:
- Removed "Top 5" selection
- Introduced **confidence-driven decisions**
- System now flags:
  - ADD (strong conviction)
  - WISHLIST (tracking candidates)

---

## Phase 19 - Wishlist System

Created:
- `data/state/wishlist.csv`

Features:
- Stores system-discovered opportunities
- Separate from portfolio
- Tracks:
  - confidence
  - price
  - signal type
  - timestamps

Types:
- STRONG → high confidence
- SPECULATIVE → lower confidence

---

## Phase 20 - Hybrid Architecture Design

Defined system split:

### Old Device (Always Running)
- Collector (hourly snapshots)
- Virtual trader engine
- Market-hour execution

### New Device (User Controlled)
- Signal generation
- Decision engine
- Portfolio tracking
- Performance analysis

---

## Phase 21 - Market Awareness

Added:
- `isNepseOpen()` integration
- Market-hour constraints (10 AM – 3 PM)

Used for:
- Virtual trader execution timing
- Fair simulation vs real trading

---

## Phase 22 - Virtual Trader Engine

Created:
- Virtual trading system using wishlist

Features:
- Uses virtual capital (initial 500k)
- Confidence-based position sizing
- Cash reserve (5%)
- T+3 settlement simulation
- Buy/Sell logic based on target allocation

Behavior:
- Can reinvest profits
- Avoids full capital deployment daily
- Adjusts exposure based on confidence

---

## Phase 23 - Wishlist Trading Logic

Rules:
- Confidence → target allocation
- Rebalancing instead of blind buying
- Supports:
  - adding positions
  - reducing positions
  - full exits

No cooldown:
- Allocation logic handles scaling naturally

---

## Phase 24 - Performance Tracking (Virtual Trader)

Created:
- `virtual_performance.json`

Tracks:
- equity curve
- realized PnL
- win/loss count
- trade count
- win rate

Added:
- trade log processing
- snapshot throttling (no spam)
- return % calculation

---

## Phase 25 - Portfolio Performance Tracking (User)

Created:
- `performance_history.csv`

Tracks:
- total invested
- current value
- pnl
- return %
- position count

Integrated into:
- `run_close.py`

Runs:
- every execution (independent of decisions)

---

## Phase 26 - System Synchronization

Ensured:
- Portfolio tracking always runs
- Performance tracking independent of signals
- No silent failures on empty outputs

---

## Phase 27 - Data Collection Upgrade

Improvement:
- Switched to **hourly snapshot collection**

Reason:
- TradeTime is accurate
- Captures intraday behavior better
- Improves signal quality

---

## Phase 28 - Scheduler + Live System Planning

Planned:
- `run_live_system.py` for old device

Responsibilities:
- Run collector hourly
- Run virtual trader hourly
- Respect market hours
- Toggle system easily

---

## Current Direction

- Evaluate signal quality using virtual trader
- Compare:
  - system performance vs real portfolio
- Improve confidence scoring using real outcomes
- Build analytics layer

---

## Next Phases

### Phase 29
- System vs Portfolio comparison engine

### Phase 30
- Equity curve visualization

### Phase 31
- Drawdown and risk metrics

### Phase 32
- Backtesting system

### Phase 33
- Dashboard (local or web)

---

## Key Lessons Learned

- Signals ≠ decisions ≠ execution
- Liquidity matters more than spikes
- Confidence is better than ranking
- Separation of concerns enables scalability
- Data quality determines strategy quality

---

## Philosophy

"Detect opportunity → evaluate confidence → simulate → validate → deploy"