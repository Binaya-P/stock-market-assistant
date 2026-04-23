# NepseAI

NepseAI is a lightweight NEPSE market workflow for:

- collecting floor-sheet snapshots
- normalizing raw CSV data
- building shared summary datasets
- generating ranked trading signals
- updating a simple portfolio state

## Entry Points

- `main.py` or `run_close.py`: run the close-session signal and decision flow
- `run_midday.py`: run a lighter midday ranking pass
- `run_data_audit.py`: inspect saved raw snapshot coverage and timing
- `run_build_summaries.py`: rebuild summary exports, validation reports, and the SQLite store
- `run_sqlite_audit.py`: inspect SQLite tables and row counts
- `collector/run_fetch_once.py`: pull one raw snapshot from the API
- `collector/run_collector.py`: start the collector and summary scheduler

## Data Layout

- `data/raw/`: raw floor-sheet snapshots
- `data/summary/`: shared summary files by timeframe
- `data/summary/archive/`: dated historical summary snapshots
- `data/state/nepseai.db`: canonical SQLite store for raw and summary data
- `data/state/portfolio.csv`: tracked portfolio state

## Current Signal Model

Signals are ranked using:

- large-trade participation
- total traded volume
- trade activity
- liquidity weighting

Current labels are `BREAKOUT`, `ACCUMULATION`, `WATCH`, and `IGNORE`.

## Notes

- Use Python `3.12` for the currently pinned dependency versions.
- Local virtual environments such as `.venv312/` should stay untracked.
- The collector stores `collectionTime` as snapshot metadata, while `tradeTime` remains the API trade-execution time.
- Overlapping raw snapshots are deduplicated by `contractId`, keeping the latest collected copy.
- Summary rollups live in one file per timeframe instead of per-stock files.
- Summary rebuilds now also emit `pipeline_run_report.csv`, `summary_health.csv`, and `validation_issues.csv`.
- Duplicate reconciliation is exported through `duplicate_contract_report.csv`.
- Scheduled summary updates also write date-stamped archive snapshots under `data/summary/archive/`.
- The canonical queryable store is now SQLite, with CSVs kept as export artifacts.
- The scheduler fetches raw data at `1:00 PM` and `3:30 PM` on trading days, syncs SQLite on each fetch, updates `daily` at `4:00 PM`, `weekly` on Fridays at `5:00 PM`, `fortnightly` on qualifying Fridays at `6:00 PM`, `monthly` on qualifying Fridays at `7:00 PM`, and `yearly` on qualifying Fridays at `8:00 PM`.
