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

Added initial tracked positions:
- `JHAPA`
- `MABEL`

---

## Phase 8 - Decision Engine

Created:
- `process_signals()`

Logic:
- New stock can become a buy candidate
- Existing stock can be upgraded or exited

---

## Phase 9 - Data Pipeline Reframe

Problem:
- Raw and cleaned data responsibilities were unclear
- Data loading was brittle

Decision:
- Stabilize raw-data access first
- Build a better summary layer before deeper signal upgrades

---

## Phase 10 - Collector Stabilization

Fixes:
- Ensured raw-data directories are created
- Cleaned up collector save behavior
- Removed risky auto-git actions from the collector path

---

## Phase 11 - Raw Data Model Cleanup

Changes:
- Separated `tradeTime` from system metadata
- Introduced `collectionTime`
- Prepared snapshot tracking capability

Reason:
- Preserve exchange event time cleanly
- Prepare better inputs for aggregation and signals

---

## Phase 12 - Summary Pipeline Foundation

Changes:
- Defined shared summary files instead of per-stock files
- Built daily stock-level summaries from raw floor-sheet data
- Added weekly, fortnightly, monthly, and yearly rollups
- Added Friday evening summary scheduling
- Set deduplication to use `contractId`
- Confirmed Python `3.12` runtime stability

Goal:
- Make summary data the stable input for future signal-engine upgrades

---

## Phase 13 - Summary Validation Iteration

- Added raw dataset reporting
- Added deduplication tracking
- Added summary health reporting
- Added validation issue detection

Outcome:
- Pipeline explains data quality and anomalies

---

## Phase 14 - SQLite Canonical Store Iteration

- Added `data/state/nepseai.db`
- Synced raw data, summaries, and reports to SQLite
- Aligned CSV exports with SQLite
- Added audit entry point

Outcome:
- Stable, queryable data foundation

---

## Phase 15 - Reconciliation Iteration

- Added duplicate contract reconciliation reporting
- Exported retained vs dropped duplicates
- Synced reconciliation data to SQLite

Outcome:
- Deduplication is now explainable, not just applied

---

## Phase 16 - Validation And Metadata Iteration

- Added stricter validation rules
- Added SQLite metadata tracking
- Improved audit visibility

Outcome:
- Safer pipeline with easier recovery

---

## Phase 17 - Scheduler And Archive Iteration

- Scheduled raw fetch at fixed trading intervals
- Synced SQLite after each run
- Added staged summary jobs
- Added archive snapshots
- Made scheduler restart-safe

Outcome:
- Fully operational data pipeline

---

## Phase 18 - Collector Intelligence Upgrade (TODAY)

Major upgrades:

### Market-Aware Collection
- Integrated NEPSE `isNepseOpen()` API
- Added fallback trading window (10:00–15:00)
- Added buffer handling for delayed API responses

### Data Integrity Improvements
- Enforced `contractId` deduplication at ingestion
- Prevented duplicate accumulation across snapshots
- Added corruption-safe CSV handling

### Metadata Enhancements
- Added `collectionTime` per snapshot
- Prepared system for `snapshotId` tracking

### Frequency Change
- Shifted from sparse collection to **hourly collection**
- Ensures near-complete trade capture while maintaining efficiency

---

## Phase 19 - Decision Engine Redesign (TODAY)

Major shift in philosophy:

### Portfolio Decoupling
- Removed automatic portfolio trading
- Portfolio is now **user-controlled only**

### Suggestion-Based System
- Introduced:
  - `ADD`
  - `REDUCE`
  - `EXIT`
  - `HOLD`

### Confidence-Based Decisions
- Removed "top N" logic
- Replaced with dynamic confidence thresholds

---

## Phase 20 - Wishlist System Introduction (TODAY)

New subsystem:

### Wishlist Engine
- Created `wishlist.csv`
- Separated from real portfolio

### Signal Classification
- `WISHLIST_STRONG`
- `WISHLIST_SPECULATIVE`

### Purpose
- Capture high-potential signals without risking real capital
- Track system intelligence independently

---

## Phase 21 - Hybrid Trading Architecture (TODAY)

Defined system structure:

### Dual System Design
1. **User Portfolio**
   - Manual control
   - Real capital
   - No auto-execution

2. **System Wishlist Trader**
   - Fully automated
   - Virtual capital
   - Performance tracking

---

## Phase 22 - Virtual Trading Engine Design (PLANNED)

Rules defined:

### Capital Model
- Initial capital: 500,000
- 5% cash reserve

### Allocation Strategy
- Confidence-weighted allocation
- Max cap per position

### Trading Rules
- Only trade between 10:00–15:00
- T+3 settlement rule enforced
- Cash returned only after settlement

### Purpose
- Measure signal quality
- Validate strategy before real capital deployment

---

## Current Direction

- Build virtual trading engine on top of wishlist
- Use performance data to refine signal engine
- Improve summary quality and scoring
- Strengthen analytics using SQLite

---

## Next Phases

### Phase 23
- Virtual trading engine implementation

### Phase 24
- Backtesting framework

### Phase 25
- Performance analytics (PnL, win rate, drawdown)

---

## Key Lessons Learned

- Raw signals ≠ tradable signals
- Liquidity is critical
- Data integrity is foundational
- Signal, decision, and execution must remain separate
- Systems should be testable without risking capital

---

## Philosophy

"Detect opportunity → evaluate risk → simulate → deploy capital"