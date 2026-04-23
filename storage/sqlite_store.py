import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd


DEFAULT_SQLITE_PATH = Path("data/state/nepseai.db")
SCHEMA_VERSION = "1"


def _ensure_parent_dir(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _write_table(conn: sqlite3.Connection, table_name: str, df: pd.DataFrame) -> None:
    df.to_sql(table_name, conn, if_exists="replace", index=False)


def _append_table(conn: sqlite3.Connection, table_name: str, df: pd.DataFrame) -> None:
    df.to_sql(table_name, conn, if_exists="append", index=False)


def _create_indexes(conn: sqlite3.Connection) -> None:
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_raw_contracts_contract_id ON raw_contracts (contractId)",
        "CREATE INDEX IF NOT EXISTS idx_raw_contracts_business_date ON raw_contracts (businessDate)",
        "CREATE INDEX IF NOT EXISTS idx_raw_contracts_symbol ON raw_contracts (stockSymbol)",
        "CREATE INDEX IF NOT EXISTS idx_snapshot_index_snapshot_id ON raw_snapshot_index (snapshotId)",
        "CREATE INDEX IF NOT EXISTS idx_duplicate_contract_report_contract_id ON duplicate_contract_report (contractId)",
        "CREATE INDEX IF NOT EXISTS idx_scheduler_job_runs_job_name ON scheduler_job_runs (job_name)",
        "CREATE INDEX IF NOT EXISTS idx_summary_daily_period_symbol ON summary_daily (period_key, stockSymbol)",
        "CREATE INDEX IF NOT EXISTS idx_summary_weekly_period_symbol ON summary_weekly (period_key, stockSymbol)",
        "CREATE INDEX IF NOT EXISTS idx_summary_fortnightly_period_symbol ON summary_fortnightly (period_key, stockSymbol)",
        "CREATE INDEX IF NOT EXISTS idx_summary_monthly_period_symbol ON summary_monthly (period_key, stockSymbol)",
        "CREATE INDEX IF NOT EXISTS idx_summary_yearly_period_symbol ON summary_yearly (period_key, stockSymbol)",
        "CREATE INDEX IF NOT EXISTS idx_validation_issues_period ON summary_validation_issues (period_type, severity)",
    ]

    for statement in statements:
        try:
            conn.execute(statement)
        except sqlite3.OperationalError:
            # Ignore missing-column issues if a table is empty or was not materialized yet.
            continue


def _ensure_metadata_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            schema_version TEXT,
            last_synced_at TEXT,
            notes TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduler_job_runs (
            job_name TEXT,
            run_at TEXT,
            period_key TEXT,
            notes TEXT
        )
        """
    )


def _refresh_pipeline_metadata(conn: sqlite3.Connection, notes: str) -> None:
    _ensure_metadata_tables(conn)
    conn.execute("DELETE FROM pipeline_metadata")
    conn.execute(
        "INSERT INTO pipeline_metadata (schema_version, last_synced_at, notes) VALUES (?, datetime('now'), ?)",
        (
            SCHEMA_VERSION,
            notes,
        ),
    )


def record_job_run(
    job_name: str,
    period_key: str = "",
    notes: str = "",
    db_path: Path = DEFAULT_SQLITE_PATH,
) -> None:
    resolved_path = Path(db_path)
    _ensure_parent_dir(resolved_path)

    with sqlite3.connect(resolved_path) as conn:
        _ensure_metadata_tables(conn)
        conn.execute(
            "INSERT INTO scheduler_job_runs (job_name, run_at, period_key, notes) VALUES (?, ?, ?, ?)",
            (
                job_name,
                datetime.now().isoformat(timespec="seconds"),
                period_key,
                notes,
            ),
        )
        conn.commit()


def get_job_run_count(job_name: str, db_path: Path = DEFAULT_SQLITE_PATH) -> int:
    resolved_path = Path(db_path)
    if not resolved_path.exists():
        return 0

    with sqlite3.connect(resolved_path) as conn:
        _ensure_metadata_tables(conn)
        row = conn.execute(
            "SELECT COUNT(*) FROM scheduler_job_runs WHERE job_name = ?",
            (job_name,),
        ).fetchone()
        return int(row[0]) if row else 0


def job_run_exists(
    job_name: str,
    period_key: str,
    db_path: Path = DEFAULT_SQLITE_PATH,
) -> bool:
    resolved_path = Path(db_path)
    if not resolved_path.exists():
        return False

    with sqlite3.connect(resolved_path) as conn:
        _ensure_metadata_tables(conn)
        row = conn.execute(
            "SELECT 1 FROM scheduler_job_runs WHERE job_name = ? AND period_key = ? LIMIT 1",
            (job_name, period_key),
        ).fetchone()
        return row is not None


def sync_raw_bundle_to_sqlite(
    data_bundle: Dict[str, object],
    db_path: Path = DEFAULT_SQLITE_PATH,
) -> Path:
    resolved_path = Path(db_path)
    _ensure_parent_dir(resolved_path)

    raw_df = data_bundle.get("raw_df", pd.DataFrame())
    snapshot_index = data_bundle.get("snapshot_index", pd.DataFrame())
    raw_dataset_report = data_bundle.get("raw_dataset_report", pd.DataFrame())
    duplicate_contract_report = data_bundle.get(
        "duplicate_contract_report", pd.DataFrame()
    )

    with sqlite3.connect(resolved_path) as conn:
        _refresh_pipeline_metadata(
            conn,
            "Canonical NepseAI raw and summary store.",
        )
        _write_table(conn, "raw_contracts", raw_df)
        _write_table(conn, "raw_snapshot_index", snapshot_index)
        _write_table(conn, "duplicate_contract_report", duplicate_contract_report)

        if isinstance(raw_dataset_report, pd.DataFrame) and not raw_dataset_report.empty:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    generated_at TEXT,
                    source_folder TEXT,
                    snapshot_count INTEGER,
                    raw_rows INTEGER,
                    deduplicated_rows INTEGER,
                    dropped_duplicate_rows INTEGER,
                    unique_contract_ids INTEGER,
                    duplicate_contract_ids INTEGER,
                    earliest_trade_time TEXT,
                    latest_trade_time TEXT,
                    earliest_collection_time TEXT,
                    latest_collection_time TEXT,
                    business_date_min TEXT,
                    business_date_max TEXT
                )
                """
            )
            _append_table(conn, "pipeline_runs", raw_dataset_report)

        _create_indexes(conn)
        conn.commit()

    return resolved_path


def sync_selected_summaries_to_sqlite(
    artifacts: Dict[str, object],
    period_types: Iterable[str],
    db_path: Path = DEFAULT_SQLITE_PATH,
) -> Path:
    resolved_path = Path(db_path)
    _ensure_parent_dir(resolved_path)

    summaries = artifacts.get("summaries", {})
    summary_health = artifacts.get("summary_health", pd.DataFrame())
    validation_issues = artifacts.get("validation_issues", pd.DataFrame())

    with sqlite3.connect(resolved_path) as conn:
        _refresh_pipeline_metadata(
            conn,
            "Canonical NepseAI raw and summary store.",
        )
        _write_table(conn, "summary_health", summary_health)
        _write_table(conn, "summary_validation_issues", validation_issues)

        if isinstance(summaries, dict):
            for period_type in period_types:
                summary_df = summaries.get(period_type, pd.DataFrame())
                _write_table(conn, f"summary_{period_type}", summary_df)

        _create_indexes(conn)
        conn.commit()

    return resolved_path


def sync_pipeline_to_sqlite(
    artifacts: Dict[str, object],
    db_path: Path = DEFAULT_SQLITE_PATH,
) -> Path:
    resolved_path = Path(db_path)
    _ensure_parent_dir(resolved_path)

    raw_df = artifacts.get("raw_df", pd.DataFrame())
    snapshot_index = artifacts.get("snapshot_index", pd.DataFrame())
    raw_dataset_report = artifacts.get("raw_dataset_report", pd.DataFrame())
    duplicate_contract_report = artifacts.get("duplicate_contract_report", pd.DataFrame())
    summaries = artifacts.get("summaries", {})
    summary_health = artifacts.get("summary_health", pd.DataFrame())
    validation_issues = artifacts.get("validation_issues", pd.DataFrame())

    with sqlite3.connect(resolved_path) as conn:
        _refresh_pipeline_metadata(
            conn,
            "Canonical NepseAI raw and summary store.",
        )
        _write_table(conn, "raw_contracts", raw_df)
        _write_table(conn, "raw_snapshot_index", snapshot_index)
        _write_table(conn, "duplicate_contract_report", duplicate_contract_report)
        _write_table(conn, "summary_health", summary_health)
        _write_table(conn, "summary_validation_issues", validation_issues)

        if isinstance(summaries, dict):
            for period_type, summary_df in summaries.items():
                _write_table(conn, f"summary_{period_type}", summary_df)

        if isinstance(raw_dataset_report, pd.DataFrame) and not raw_dataset_report.empty:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    generated_at TEXT,
                    source_folder TEXT,
                    snapshot_count INTEGER,
                    raw_rows INTEGER,
                    deduplicated_rows INTEGER,
                    dropped_duplicate_rows INTEGER,
                    unique_contract_ids INTEGER,
                    duplicate_contract_ids INTEGER,
                    earliest_trade_time TEXT,
                    latest_trade_time TEXT,
                    earliest_collection_time TEXT,
                    latest_collection_time TEXT,
                    business_date_min TEXT,
                    business_date_max TEXT
                )
                """
            )
            _append_table(conn, "pipeline_runs", raw_dataset_report)

        _create_indexes(conn)
        conn.commit()

    return resolved_path
