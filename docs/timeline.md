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
- Separated `tradeTime` from collection metadata
- Introduced `collectionTime` and `snapshotId`
- Added raw snapshot audit support

Reason:
- Preserve exchange event time cleanly
- Prepare better inputs for later aggregation

---

## Phase 12 - Summary Pipeline Foundation

Changes:
- Defined shared summary files instead of per-stock files
- Built daily stock-level summaries from raw floor-sheet data
- Added weekly, fortnightly, monthly, and yearly rollups
- Added Friday evening summary scheduling
- Set deduplication to use `contractId` across overlapping snapshots
- Confirmed Python 3.12 runtime

Goal:
- Make summary data the stable input for future signal-engine upgrades

---

## Phase 13 - Summary Validation Iteration

Iteration 1:
- Added raw dataset reporting with deduplication totals
- Expanded snapshot indexing with retained vs dropped rows
- Added summary health reporting
- Added validation issue reporting

Outcome:
- Pipeline now explains data quality and anomalies

---

## Phase 14 - SQLite Canonical Store

Iteration 2:
- Added `data/state/nepseai.db`
- Synced raw, summaries, and reports into SQLite
- Aligned CSV exports with SQLite
- Added SQLite audit tool

Outcome:
- Stable queryable data layer

---

## Phase 15 - Reconciliation Iteration

Iteration 3:
- Added duplicate contract reconciliation
- Exported retained vs dropped contracts
- Synced to SQLite

Outcome:
- Deduplication is now explainable

---

## Phase 16 - Validation + Metadata

Iteration 4:
- Added stricter validation rules
- Added SQLite metadata tracking
- Improved audit visibility

Outcome:
- Safer and more maintainable pipeline

---

## Phase 17 - Scheduler + Automation

Iteration 5:
- Raw fetch at 1:00 PM and 3:30 PM
- Auto SQLite sync after fetch
- Scheduled summary jobs (daily → yearly)
- Archive snapshots with timestamps
- Restart-safe scheduler using job tracking

Outcome:
- Fully operational data pipeline

---

## Phase 18 - Signal + Decision System Upgrade (Today)

Major Changes:

### 1. Decision System Redesign
- Removed automatic trading behavior
- Portfolio is now **user-controlled only**
- System no longer forces BUY into portfolio

### 2. Wishlist System Introduced
- Created `wishlist.csv`
- System BUY signals go to wishlist instead of portfolio
- Portfolio = real trades
- Wishlist = system predictions

### 3. Hybrid Trading Model
- Two independent layers:
  - **User Portfolio (manual control)**
  - **System Wishlist (auto simulation)**

### 4. Virtual Capital Engine (Planned Behavior)
- Wishlist gets virtual capital = **500,000**
- Keeps **5% cash reserve**
- Uses **confidence-weighted allocation**
- Max cap per position enforced

### 5. Virtual Trading Rules
- BUY from signals
- SELL based on:
  - Confidence drop
  - Signal downgrade (`IGNORE`)
- Enforce **T+3 settlement rule**
  - Cash locked after sell
  - Released after T+3 days

### 6. System Performance Tracking
- Wishlist acts as:
  - Backtesting layer (forward testing)
  - Strategy evaluator
- Enables comparison:
  - System vs User decisions

---

## Current Direction

- Separate system intelligence from user execution
- Use wishlist as AI trading simulation
- Keep portfolio human-controlled
- Improve confidence-driven allocation

---

## Next Phases

### Phase 19
- Implement full wishlist engine (cash, trades, T+3)
- Add wishlist PnL tracking
- Add trade logs

### Phase 20
- Market regime detection (bull/bear/sideways)
- Dynamic confidence adjustment

### Phase 21
- Backtesting engine using historical summaries
- Strategy comparison framework

### Phase 22
- Performance dashboards (daily/weekly/monthly/yearly)
- Portfolio vs wishlist benchmarking

---

## Key Lessons Learned

- Raw signals ≠ tradable signals
- Liquidity > hype trades
- Separation of concerns is critical:
  - Signals ≠ Decisions ≠ Execution
- Data quality directly impacts strategy quality
- System should suggest, not force trades

---

## Philosophy

"Detect opportunity -> evaluate risk -> simulate -> then deploy capital"