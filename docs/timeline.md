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
- Confirmed the working project runtime on Python `3.12`

Goal:
- Make summary data the stable input for future signal-engine upgrades

---

## Phase 13 - Summary Validation Iteration

Iteration 1:
- added raw dataset reporting with deduplication totals
- expanded snapshot indexing with retained versus dropped rows
- added summary health reporting by timeframe
- added validation issue reporting for summary anomalies

Outcome:
- the summary pipeline now explains what it built and where data quality problems appear

---

## Phase 14 - SQLite Canonical Store Iteration

Iteration 2:
- added `data/state/nepseai.db` as the canonical local store
- synced deduplicated raw contracts into SQLite
- synced snapshot index, summary tables, health reports, and validation issues into SQLite
- updated the summary rebuild path so CSV exports and SQLite stay aligned
- added a lightweight SQLite audit entry point for quick verification

Outcome:
- the project now has a stable queryable store for collection and summarization work

---

## Phase 15 - Reconciliation Iteration

Iteration 3:
- added duplicate contract reconciliation reporting
- exported retained versus dropped duplicate contract details to CSV
- synced duplicate contract reconciliation data into SQLite

Outcome:
- the summary pipeline can now explain deduplication decisions instead of only reporting totals

---

## Phase 16 - Validation And Metadata Iteration

Iteration 4:
- added stricter summary validation for duplicate keys and invalid time windows
- added SQLite pipeline metadata for schema tracking and safer recovery
- improved SQLite audit output to show the active database path

Outcome:
- the summary system is easier to verify and safer to recover if pipeline behavior changes later

---

## Phase 17 - Scheduler And Archive Iteration

Iteration 5:
- moved raw fetch scheduling to `1:00 PM` and `3:30 PM` on trading days
- synced SQLite after each scheduled raw fetch
- added staged summary jobs for daily, weekly, fortnightly, monthly, and yearly updates
- added date-stamped archived summary snapshots for scheduled summary runs
- made scheduler jobs restart-safe through persisted SQLite job-run tracking

Outcome:
- collection, summarization, archival, and scheduling now follow a much more operational workflow

---

## Current Direction

- keep iterating on summary quality and validation depth
- use SQLite as the stable foundation for later analytics
- re-enter signal-engine work on top of stronger summary data

---

## Next Phases

### Phase 18
- Market mode detection
- Stronger signal-engine redesign

### Phase 19
- Advanced summary scoring and reconciliation tooling
- SQLite-backed analytics helpers

### Phase 20
- Backtesting system

### Phase 21
- Performance tracking across daily, weekly, monthly, and yearly views

---

## Key Lessons Learned

- Raw signals are not the same as tradable signals
- Liquidity matters more than isolated big trades
- Signal logic, decisions, and execution should stay separated
- Clean data structures make later strategy work easier

---

## Philosophy

"Detect opportunity -> evaluate risk -> allocate capital"
