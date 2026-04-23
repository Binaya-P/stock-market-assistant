from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


REQUIRED_COLUMNS = {
    "contractId",
    "stockSymbol",
    "contractQuantity",
    "contractRate",
    "tradeTime",
}

NUMERIC_COLUMNS = [
    "contractId",
    "contractQuantity",
    "contractRate",
    "contractAmount",
    "tradeBookId",
    "stockId",
]

SNAPSHOT_ID_FORMAT = "%Y%m%d_%H%M%S"

SNAPSHOT_INDEX_COLUMNS = [
    "source_file",
    "snapshotId",
    "collectionTime",
    "businessDate",
    "raw_rows",
    "unique_contracts",
    "duplicate_rows_in_snapshot",
    "cross_snapshot_duplicate_rows",
    "retained_rows_after_dedup",
    "dropped_rows_after_dedup",
    "symbols",
    "firstTradeTime",
    "lastTradeTime",
]

DUPLICATE_CONTRACT_REPORT_COLUMNS = [
    "contractId",
    "occurrence_count",
    "retained_source_file",
    "retained_snapshotId",
    "retained_collectionTime",
    "retained_tradeTime",
    "dropped_source_files",
    "dropped_snapshotIds",
    "first_seen_collectionTime",
    "last_seen_collectionTime",
]

RAW_DATASET_REPORT_COLUMNS = [
    "generated_at",
    "source_folder",
    "snapshot_count",
    "raw_rows",
    "deduplicated_rows",
    "dropped_duplicate_rows",
    "unique_contract_ids",
    "duplicate_contract_ids",
    "earliest_trade_time",
    "latest_trade_time",
    "earliest_collection_time",
    "latest_collection_time",
    "business_date_min",
    "business_date_max",
]


def _discover_floor_files(folder_path: str) -> List[Path]:
    base_path = Path(folder_path)

    if not base_path.exists():
        raise FileNotFoundError(f"Data folder not found: {base_path}")

    candidate_paths: List[Path] = []

    if base_path.is_dir():
        raw_path = base_path / "raw"
        if raw_path.exists():
            candidate_paths.extend(sorted(raw_path.glob("floor*.csv")))

        candidate_paths.extend(sorted(base_path.glob("floor*.csv")))

    unique_paths = list(dict.fromkeys(candidate_paths))

    if not unique_paths:
        raise FileNotFoundError(
            f"No floor sheet CSV files found under: {base_path}"
        )

    return unique_paths


def _extract_snapshot_id(source_file: Path) -> Optional[str]:
    stem = source_file.stem

    if stem.startswith("floor_"):
        return stem.replace("floor_", "", 1)

    return None


def _parse_snapshot_id(snapshot_id: Optional[str]) -> Optional[datetime]:
    if not snapshot_id:
        return None

    try:
        return datetime.strptime(snapshot_id, SNAPSHOT_ID_FORMAT)
    except ValueError:
        return None


def _normalize_collection_time(series: pd.Series) -> pd.Series:
    values = series.astype(str).str.strip()

    parsed = pd.to_datetime(values, errors="coerce", utc=True)

    needs_snapshot_parse = parsed.isna() & values.ne("") & values.ne("None")
    if needs_snapshot_parse.any():
        parsed.loc[needs_snapshot_parse] = pd.to_datetime(
            values.loc[needs_snapshot_parse],
            format=SNAPSHOT_ID_FORMAT,
            errors="coerce",
            utc=True
        )

    # 🔥 CRITICAL FIX: make everything tz-naive (consistent)
    parsed = parsed.dt.tz_localize(None)

    return parsed


def _prepare_frame(df: pd.DataFrame, source_file: Path) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(
            f"{source_file.name} is missing required columns: {missing_list}"
        )

    cleaned = df.copy()

    for column in NUMERIC_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned["tradeTime"] = pd.to_datetime(cleaned["tradeTime"], errors="coerce", utc=True).dt.tz_localize(None)

    if "businessDate" in cleaned.columns:
        cleaned["businessDate"] = pd.to_datetime(
            cleaned["businessDate"], errors="coerce"
        )

    if "collectionTime" not in cleaned.columns and "timestamp" in cleaned.columns:
        cleaned["collectionTime"] = cleaned["timestamp"]

    snapshot_id = _extract_snapshot_id(source_file)

    if "collectionTime" not in cleaned.columns:
        fallback_collection_time = _parse_snapshot_id(snapshot_id)
        cleaned["collectionTime"] = (
            fallback_collection_time.isoformat() if fallback_collection_time else None
        )

    cleaned["collectionTime"] = _normalize_collection_time(cleaned["collectionTime"])
    cleaned["snapshotId"] = snapshot_id
    cleaned["source_file"] = source_file.name

    if "timestamp" in cleaned.columns:
        cleaned = cleaned.drop(columns=["timestamp"])

    cleaned = cleaned.dropna(
        subset=["stockSymbol", "contractQuantity", "contractRate", "tradeTime"]
    )

    cleaned["stockSymbol"] = cleaned["stockSymbol"].astype(str).str.strip().str.upper()

    return cleaned


def _load_prepared_frames(folder_path: str) -> List[Tuple[Path, pd.DataFrame]]:
    prepared_frames: List[Tuple[Path, pd.DataFrame]] = []

    for file_path in _discover_floor_files(folder_path):
        frame = pd.read_csv(file_path)
        prepared_frames.append((file_path, _prepare_frame(frame, file_path)))

    return prepared_frames


def _empty_snapshot_index() -> pd.DataFrame:
    return pd.DataFrame(columns=SNAPSHOT_INDEX_COLUMNS)


def _empty_raw_dataset_report(folder_path: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "source_folder": str(Path(folder_path)),
                "snapshot_count": 0,
                "raw_rows": 0,
                "deduplicated_rows": 0,
                "dropped_duplicate_rows": 0,
                "unique_contract_ids": 0,
                "duplicate_contract_ids": 0,
                "earliest_trade_time": pd.NaT,
                "latest_trade_time": pd.NaT,
                "earliest_collection_time": pd.NaT,
                "latest_collection_time": pd.NaT,
                "business_date_min": pd.NaT,
                "business_date_max": pd.NaT,
            }
        ],
        columns=RAW_DATASET_REPORT_COLUMNS,
    )


def _empty_duplicate_contract_report() -> pd.DataFrame:
    return pd.DataFrame(columns=DUPLICATE_CONTRACT_REPORT_COLUMNS)


def _combine_prepared_frames(prepared_frames: List[Tuple[Path, pd.DataFrame]]) -> pd.DataFrame:
    if not prepared_frames:
        return pd.DataFrame()

    combined = pd.concat(
        [frame for _, frame in prepared_frames],
        ignore_index=True,
    )
    combined["__row_id"] = range(len(combined))
    return combined


def _deduplicate_contracts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "contractId" not in df.columns:
        return df

    working = df.copy()
    working["collectionTime"] = pd.to_datetime(
        working["collectionTime"], errors="coerce"
    )
    working["tradeTime"] = pd.to_datetime(working["tradeTime"], errors="coerce")

    working = working.sort_values(
        by=["contractId", "collectionTime", "tradeTime", "source_file", "__row_id"],
        ascending=[True, True, True, True, True],
        na_position="first",
    )

    return working.drop_duplicates(subset=["contractId"], keep="last").reset_index(
        drop=True
    )


def _build_snapshot_index_from_combined(
    combined: pd.DataFrame,
    deduplicated: pd.DataFrame,
) -> pd.DataFrame:
    if combined.empty:
        return _empty_snapshot_index()

    duplicate_contract_ids = set(
        combined["contractId"].value_counts().loc[lambda s: s > 1].index.tolist()
    )
    retained_row_ids = set(deduplicated["__row_id"].tolist()) if "__row_id" in deduplicated.columns else set()

    snapshot_rows = []
    grouped = combined.groupby("source_file", sort=False)

    for source_file, frame in grouped:
        snapshot_rows.append(
            {
                "source_file": source_file,
                "snapshotId": frame["snapshotId"].iloc[0] if not frame.empty else None,
                "collectionTime": (
                    frame["collectionTime"].mode().iloc[0]
                    if frame["collectionTime"].notna().any()
                    else pd.NaT
                ),
                "businessDate": (
                    frame["businessDate"].mode().iloc[0]
                    if "businessDate" in frame.columns and frame["businessDate"].notna().any()
                    else pd.NaT
                ),
                "raw_rows": len(frame),
                "unique_contracts": frame["contractId"].nunique(),
                "duplicate_rows_in_snapshot": len(frame) - frame["contractId"].nunique(),
                "cross_snapshot_duplicate_rows": int(
                    frame["contractId"].isin(duplicate_contract_ids).sum()
                ),
                "retained_rows_after_dedup": int(
                    frame["__row_id"].isin(retained_row_ids).sum()
                ),
                "dropped_rows_after_dedup": int(
                    len(frame) - frame["__row_id"].isin(retained_row_ids).sum()
                ),
                "symbols": frame["stockSymbol"].nunique(),
                "firstTradeTime": frame["tradeTime"].min(),
                "lastTradeTime": frame["tradeTime"].max(),
            }
        )

    return pd.DataFrame(snapshot_rows, columns=SNAPSHOT_INDEX_COLUMNS).sort_values(
        by=["collectionTime", "source_file"],
        ascending=[False, False],
    ).reset_index(drop=True)


def _build_raw_dataset_report_from_combined(
    combined: pd.DataFrame,
    deduplicated: pd.DataFrame,
    folder_path: str,
) -> pd.DataFrame:
    if combined.empty:
        return _empty_raw_dataset_report(folder_path)

    contract_counts = combined["contractId"].value_counts()

    return pd.DataFrame(
        [
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "source_folder": str(Path(folder_path)),
                "snapshot_count": combined["source_file"].nunique(),
                "raw_rows": len(combined),
                "deduplicated_rows": len(deduplicated),
                "dropped_duplicate_rows": len(combined) - len(deduplicated),
                "unique_contract_ids": combined["contractId"].nunique(),
                "duplicate_contract_ids": int((contract_counts > 1).sum()),
                "earliest_trade_time": combined["tradeTime"].min(),
                "latest_trade_time": combined["tradeTime"].max(),
                "earliest_collection_time": combined["collectionTime"].min(),
                "latest_collection_time": combined["collectionTime"].max(),
                "business_date_min": combined["businessDate"].min()
                if "businessDate" in combined.columns
                else pd.NaT,
                "business_date_max": combined["businessDate"].max()
                if "businessDate" in combined.columns
                else pd.NaT,
            }
        ],
        columns=RAW_DATASET_REPORT_COLUMNS,
    )


def _build_duplicate_contract_report(
    combined: pd.DataFrame,
    deduplicated: pd.DataFrame,
) -> pd.DataFrame:
    if combined.empty:
        return _empty_duplicate_contract_report()

    contract_counts = combined["contractId"].value_counts()
    duplicate_ids = contract_counts.loc[contract_counts > 1].index.tolist()

    if not duplicate_ids:
        return _empty_duplicate_contract_report()

    retained_lookup = (
        deduplicated[
            [
                "contractId",
                "__row_id",
                "source_file",
                "snapshotId",
                "collectionTime",
                "tradeTime",
            ]
        ]
        .rename(
            columns={
                "__row_id": "retained_row_id",
                "source_file": "retained_source_file",
                "snapshotId": "retained_snapshotId",
                "collectionTime": "retained_collectionTime",
                "tradeTime": "retained_tradeTime",
            }
        )
        .set_index("contractId")
    )

    duplicate_frame = combined[combined["contractId"].isin(duplicate_ids)].copy()
    duplicate_frame = duplicate_frame.merge(
        retained_lookup.reset_index(),
        on="contractId",
        how="left",
    )
    duplicate_frame["is_retained_row"] = (
        duplicate_frame["__row_id"] == duplicate_frame["retained_row_id"]
    )

    occurrence_counts = (
        duplicate_frame.groupby("contractId").size().rename("occurrence_count")
    )

    dropped_rows = duplicate_frame[~duplicate_frame["is_retained_row"]].copy()
    if dropped_rows.empty:
        dropped_agg = pd.DataFrame(
            columns=["contractId", "dropped_source_files", "dropped_snapshotIds"]
        )
    else:
        dropped_agg = (
            dropped_rows.groupby("contractId", as_index=False)
            .agg(
                dropped_source_files=(
                    "source_file",
                    lambda s: "|".join(s.astype(str).tolist()),
                ),
                dropped_snapshotIds=(
                    "snapshotId",
                    lambda s: "|".join(s.fillna("").astype(str).tolist()),
                ),
            )
        )

    retained_rows = (
        duplicate_frame[duplicate_frame["is_retained_row"]]
        .drop_duplicates(subset=["contractId"])
        .loc[
            :,
            [
                "contractId",
                "retained_source_file",
                "retained_snapshotId",
                "retained_collectionTime",
                "retained_tradeTime",
            ],
        ]
    )

    seen_window = (
        duplicate_frame.groupby("contractId", as_index=False)
        .agg(
            first_seen_collectionTime=("collectionTime", "min"),
            last_seen_collectionTime=("collectionTime", "max"),
        )
    )

    report = retained_rows.merge(
        occurrence_counts.reset_index(),
        on="contractId",
        how="left",
    ).merge(
        dropped_agg,
        on="contractId",
        how="left",
    ).merge(
        seen_window,
        on="contractId",
        how="left",
    )

    report["dropped_source_files"] = report["dropped_source_files"].fillna("")
    report["dropped_snapshotIds"] = report["dropped_snapshotIds"].fillna("")

    return report[DUPLICATE_CONTRACT_REPORT_COLUMNS].sort_values(
        by=["occurrence_count", "contractId"],
        ascending=[False, True],
    ).reset_index(drop=True)


def load_data_bundle(folder_path: str = "data/raw/") -> Dict[str, pd.DataFrame]:
    prepared_frames = _load_prepared_frames(folder_path)
    combined = _combine_prepared_frames(prepared_frames)

    if combined.empty:
        return {
            "raw_df": pd.DataFrame(),
            "snapshot_index": _empty_snapshot_index(),
            "raw_dataset_report": _empty_raw_dataset_report(folder_path),
            "duplicate_contract_report": _empty_duplicate_contract_report(),
        }

    deduplicated = _deduplicate_contracts(combined)
    snapshot_index = _build_snapshot_index_from_combined(combined, deduplicated)
    raw_dataset_report = _build_raw_dataset_report_from_combined(
        combined,
        deduplicated,
        folder_path,
    )
    duplicate_contract_report = _build_duplicate_contract_report(combined, deduplicated)

    raw_df = deduplicated.drop(columns=["__row_id"], errors="ignore").sort_values(
        by=["tradeTime", "contractId"],
        ascending=[True, True],
    ).reset_index(drop=True)

    return {
        "raw_df": raw_df,
        "snapshot_index": snapshot_index,
        "raw_dataset_report": raw_dataset_report,
        "duplicate_contract_report": duplicate_contract_report,
    }


def load_all_data(folder_path: str = "data/raw/") -> pd.DataFrame:
    return load_data_bundle(folder_path)["raw_df"]


def build_snapshot_index(folder_path: str = "data/raw/") -> pd.DataFrame:
    return load_data_bundle(folder_path)["snapshot_index"]


def build_raw_dataset_report(folder_path: str = "data/raw/") -> pd.DataFrame:
    return load_data_bundle(folder_path)["raw_dataset_report"]


def build_duplicate_contract_report(folder_path: str = "data/raw/") -> pd.DataFrame:
    return load_data_bundle(folder_path)["duplicate_contract_report"]
