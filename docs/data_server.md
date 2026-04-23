# Data Pipeline

## Overview

Handles collection, storage, and preparation of floor-sheet data for signal generation.

## Current Structure

`data/`

- `raw/`: timestamped NEPSE floor-sheet snapshots
- `summary/`: shared summary files by timeframe
- `summary/archive/`: dated historical summary snapshots
- `state/nepseai.db`: canonical SQLite store for raw and summary data
- `state/portfolio.csv`: persistent portfolio state

## Data Flow

`NEPSE API -> Collector -> Raw CSV snapshots -> Deduplicated data bundle -> Summary files + SQLite -> Analysis Engine`

## Raw Data Collection

Using the NEPSE floor-sheet endpoint:

- collected manually or through the scheduler
- saved as `data/raw/floor_YYYYMMDD_HHMMSS.csv`
- enriched with `collectionTime` and `snapshotId` for snapshot tracking

`tradeTime` remains the exchange-reported trade execution time from the API.

When multiple raw snapshots contain the same trade, the loader deduplicates by `contractId` and keeps the latest collected version.

## Summary Data

Summary datasets are stored as shared files, not one file per stock:

- `data/summary/daily_summary.csv`
- `data/summary/weekly_summary.csv`
- `data/summary/fortnightly_summary.csv`
- `data/summary/monthly_summary.csv`
- `data/summary/yearly_summary.csv`
- `data/summary/pipeline_run_report.csv`
- `data/summary/summary_health.csv`
- `data/summary/validation_issues.csv`
- `data/summary/duplicate_contract_report.csv`

Each file contains rows for all stocks in that timeframe.

The latest file for each timeframe remains in place, and scheduled summary updates also archive a date-stamped historical copy.

The daily summary is built from raw floor-sheet trades and includes:

- stock-level open, close, high, and low prices
- trades, volume, turnover, and snapshot coverage
- collection-time coverage
- that day signal scores for every stock

Higher summaries are rolled up from lower summary layers so the system can scale without creating many files.

## Validation And Health

The summary build now produces:

- a pipeline run report with raw row counts and deduplication totals
- a summary health report with row counts, issue counts, and coverage by timeframe
- a validation issue report for period, metric, and price-band anomalies
- a duplicate contract reconciliation report showing what was retained and what was dropped

This makes the summary system easier to audit before signal-engine upgrades.

## SQLite Store

`data/state/nepseai.db` is now the canonical local data store.

It currently holds:

- deduplicated raw contracts
- raw snapshot index data
- duplicate contract reconciliation data
- one table per summary timeframe
- summary health data
- validation issues
- pipeline run history
- scheduler job run history

## Scheduling

The scheduler now has two responsibilities:

- fetch raw floor-sheet data at `1:00 PM` and `3:30 PM` on trading days
- sync raw data into SQLite after each fetch
- update `daily_summary` on trading days at `4:00 PM`
- update `weekly_summary` on Fridays at `5:00 PM`
- update `fortnightly_summary` after every 2 weekly summary runs on Fridays at `6:00 PM`
- update `monthly_summary` after every 2 fortnightly summary runs on Fridays at `7:00 PM`
- update `yearly_summary` after every 12 monthly summary runs on Fridays at `8:00 PM`

Weekly summaries are built from daily summaries, fortnightly summaries from weekly summaries, monthly summaries from daily summaries, and yearly summaries from monthly summaries.

## State Management

`portfolio.csv` stores:

- `symbol`
- `quantity`
- `avg_price`
- `current_price`
- `confidence`
- `signal_type`
- `last_updated`

## Still Missing

- stronger runtime monitoring for collection jobs
- more advanced market-aware scoring on top of the stabilized summary layer

## Future Roadmap

### Time-based aggregation

- daily summary
- weekly summary
- fortnightly summary
- monthly summary
- yearly summary

### Automation

- scheduled collector
- Friday evening summary rollups
- optional reporting/export automation

## Key Principle

Data integrity first, signals later.
