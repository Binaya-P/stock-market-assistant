from pathlib import Path
from typing import Dict

import pandas as pd

from analysis.data_loader import load_data_bundle


SUMMARY_DIR = Path("data/summary")
SUMMARY_ARCHIVE_DIR = SUMMARY_DIR / "archive"
SUMMARY_FILES = {
    "daily": SUMMARY_DIR / "daily_summary.csv",
    "weekly": SUMMARY_DIR / "weekly_summary.csv",
    "fortnightly": SUMMARY_DIR / "fortnightly_summary.csv",
    "monthly": SUMMARY_DIR / "monthly_summary.csv",
    "yearly": SUMMARY_DIR / "yearly_summary.csv",
}

PIPELINE_REPORT_FILE = SUMMARY_DIR / "pipeline_run_report.csv"
SUMMARY_HEALTH_FILE = SUMMARY_DIR / "summary_health.csv"
VALIDATION_ISSUES_FILE = SUMMARY_DIR / "validation_issues.csv"
DUPLICATE_CONTRACT_REPORT_FILE = SUMMARY_DIR / "duplicate_contract_report.csv"

SUMMARY_COLUMNS = [
    "period_type",
    "period_key",
    "period_start",
    "period_end",
    "stockSymbol",
    "securityName",
    "trading_days",
    "snapshot_count",
    "total_trades",
    "total_volume",
    "total_turnover",
    "avg_price",
    "open_price",
    "close_price",
    "high_price",
    "low_price",
    "first_trade_time",
    "last_trade_time",
    "first_collection_time",
    "last_collection_time",
    "confidence_sum",
    "avg_confidence",
    "max_confidence",
    "last_confidence",
    "final_score_sum",
    "avg_final_score",
    "max_final_score",
    "last_final_score",
    "positive_signal_days",
    "breakout_days",
    "accumulation_days",
    "watch_days",
    "ignore_days",
    "latest_signal",
]

VALIDATION_COLUMNS = [
    "severity",
    "scope",
    "period_type",
    "period_key",
    "stockSymbol",
    "issue_type",
    "detail",
]

SUMMARY_HEALTH_COLUMNS = [
    "period_type",
    "row_count",
    "period_count",
    "unique_symbols",
    "total_trades",
    "total_volume",
    "issue_count",
    "error_count",
    "warning_count",
    "latest_period_start",
    "latest_period_end",
]


def _empty_summary_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=SUMMARY_COLUMNS)


def _empty_validation_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=VALIDATION_COLUMNS)


def _ensure_summary_dir() -> None:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    safe_denominator = denominator.replace(0, pd.NA)
    return (numerator / safe_denominator).fillna(0.0)


def _last_non_empty(series: pd.Series) -> str:
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""]
    if values.empty:
        return ""
    return values.iloc[-1]


def _round_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    rounded = df.copy()
    decimal_columns = [
        "total_turnover",
        "avg_price",
        "open_price",
        "close_price",
        "high_price",
        "low_price",
        "confidence_sum",
        "avg_confidence",
        "max_confidence",
        "last_confidence",
        "final_score_sum",
        "avg_final_score",
        "max_final_score",
        "last_final_score",
    ]

    for column in decimal_columns:
        if column in rounded.columns:
            rounded[column] = pd.to_numeric(rounded[column], errors="coerce").round(2)

    return rounded


def _normalize_period_columns(summary_df: pd.DataFrame) -> pd.DataFrame:
    normalized = summary_df.copy()
    for column in [
        "period_start",
        "period_end",
        "first_trade_time",
        "last_trade_time",
        "first_collection_time",
        "last_collection_time",
    ]:
        normalized[column] = pd.to_datetime(normalized[column], errors="coerce")
    return normalized


def _score_signal_row(row: pd.Series) -> pd.Series:
    volume = float(row["total_volume"])
    trades = float(row["total_trades"])
    if volume <= 0 or trades <= 0:
        return pd.Series(
            {
                "confidence": 0.0,
                "final_score": 0.0,
                "system_signal": "IGNORE",
            }
        )

    price_span = max(float(row["high_price"]) - float(row["low_price"]), 0.0)
    avg_price = float(row["avg_price"])
    price_span_ratio = price_span / avg_price if avg_price > 0 else 0.0
    close_position = (
        (float(row["close_price"]) - float(row["low_price"])) / price_span
        if price_span > 0
        else 0.5
    )
    turnover_per_trade = float(row["total_turnover"]) / trades if trades > 0 else 0.0
    turnover_per_volume = float(row["total_turnover"]) / volume if volume > 0 else 0.0

    confidence = min(
        100.0,
        (min(price_span_ratio, 0.15) / 0.15) * 25.0
        + close_position * 35.0
        + min(turnover_per_trade / max(avg_price, 1.0), 1.0) * 20.0
        + min(turnover_per_volume / max(avg_price, 1.0), 1.0) * 20.0,
    )

    final_score = min(
        100.0,
        confidence * 0.7
        + min((volume / 500000.0) * 100.0, 100.0) * 0.15
        + min((trades / 1000.0) * 100.0, 100.0) * 0.15,
    )

    if final_score >= 75 and close_position >= 0.6:
        signal = "BREAKOUT"
    elif confidence >= 45:
        signal = "ACCUMULATION"
    elif confidence >= 35:
        signal = "WATCH"
    else:
        signal = "IGNORE"

    return pd.Series(
        {
            "confidence": round(confidence, 2),
            "final_score": round(final_score, 2),
            "system_signal": signal,
        }
    )


def _with_period_metadata(summary_df: pd.DataFrame, period_type: str) -> pd.DataFrame:
    enriched = summary_df.copy()
    source_dates = pd.to_datetime(enriched["period_start"]).dt.normalize()

    if period_type == "weekly":
        enriched["period_start"] = source_dates - pd.to_timedelta(
            source_dates.dt.weekday, unit="D"
        )
        enriched["period_end"] = enriched["period_start"] + pd.Timedelta(days=4)
        iso = enriched["period_start"].dt.isocalendar()
        enriched["period_key"] = (
            iso["year"].astype(str)
            + "-W"
            + iso["week"].astype(str).str.zfill(2)
        )
    elif period_type == "fortnightly":
        iso = source_dates.dt.isocalendar()
        week_index = iso["week"].astype(int)
        week_pair_offset = ((week_index - 1) % 2) * 7
        fortnight_number = ((week_index - 1) // 2 + 1).astype(int)
        enriched["period_start"] = source_dates - pd.to_timedelta(
            source_dates.dt.weekday + week_pair_offset, unit="D"
        )
        enriched["period_end"] = enriched["period_start"] + pd.Timedelta(days=11)
        enriched["period_key"] = (
            iso["year"].astype(str)
            + "-FN"
            + fortnight_number.astype(str).str.zfill(2)
        )
    elif period_type == "monthly":
        month_period = source_dates.dt.to_period("M")
        enriched["period_start"] = month_period.dt.to_timestamp()
        enriched["period_end"] = (
            month_period.dt.to_timestamp() + pd.offsets.MonthEnd(0)
        )
        enriched["period_key"] = month_period.astype(str)
    elif period_type == "yearly":
        years = source_dates.dt.year.astype(str)
        enriched["period_start"] = pd.to_datetime(years + "-01-01")
        enriched["period_end"] = pd.to_datetime(years + "-12-31")
        enriched["period_key"] = years
    else:
        raise ValueError(f"Unsupported period type: {period_type}")

    return enriched


def build_daily_summary_from_raw(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return _empty_summary_frame()

    working = raw_df.copy()
    working["businessDate"] = pd.to_datetime(working["businessDate"]).dt.normalize()
    working["tradeTime"] = pd.to_datetime(working["tradeTime"])
    working["collectionTime"] = pd.to_datetime(working["collectionTime"])

    if "contractAmount" not in working.columns:
        working["contractAmount"] = (
            working["contractQuantity"] * working["contractRate"]
        )

    working["contractAmount"] = (
        pd.to_numeric(working["contractAmount"], errors="coerce")
        .fillna(working["contractQuantity"] * working["contractRate"])
    )

    if "securityName" not in working.columns:
        working["securityName"] = ""
    else:
        working["securityName"] = working["securityName"].fillna("").astype(str)

    working = working.sort_values(
        by=["businessDate", "stockSymbol", "tradeTime", "contractId"],
        ascending=[True, True, True, True],
    )

    daily = (
        working.groupby(["businessDate", "stockSymbol"], as_index=False)
        .agg(
            securityName=("securityName", _last_non_empty),
            snapshot_count=("snapshotId", "nunique"),
            total_trades=("contractId", "count"),
            total_volume=("contractQuantity", "sum"),
            total_turnover=("contractAmount", "sum"),
            open_price=("contractRate", "first"),
            close_price=("contractRate", "last"),
            high_price=("contractRate", "max"),
            low_price=("contractRate", "min"),
            first_trade_time=("tradeTime", "min"),
            last_trade_time=("tradeTime", "max"),
            first_collection_time=("collectionTime", "min"),
            last_collection_time=("collectionTime", "max"),
        )
    )

    daily["avg_price"] = _safe_divide(daily["total_turnover"], daily["total_volume"])

    scored = daily.apply(_score_signal_row, axis=1)
    daily = pd.concat([daily, scored], axis=1)

    daily["period_type"] = "daily"
    daily["period_key"] = daily["businessDate"].dt.strftime("%Y-%m-%d")
    daily["period_start"] = daily["businessDate"]
    daily["period_end"] = daily["businessDate"]
    daily["trading_days"] = 1
    daily["confidence_sum"] = daily["confidence"]
    daily["avg_confidence"] = daily["confidence"]
    daily["max_confidence"] = daily["confidence"]
    daily["last_confidence"] = daily["confidence"]
    daily["final_score_sum"] = daily["final_score"]
    daily["avg_final_score"] = daily["final_score"]
    daily["max_final_score"] = daily["final_score"]
    daily["last_final_score"] = daily["final_score"]
    daily["positive_signal_days"] = (daily["system_signal"] != "IGNORE").astype(int)
    daily["breakout_days"] = (daily["system_signal"] == "BREAKOUT").astype(int)
    daily["accumulation_days"] = (daily["system_signal"] == "ACCUMULATION").astype(int)
    daily["watch_days"] = (daily["system_signal"] == "WATCH").astype(int)
    daily["ignore_days"] = (daily["system_signal"] == "IGNORE").astype(int)
    daily["latest_signal"] = daily["system_signal"]

    daily = daily[SUMMARY_COLUMNS]

    return _round_numeric_columns(
        daily.sort_values(
            by=["period_start", "total_volume", "stockSymbol"],
            ascending=[False, False, True],
        ).reset_index(drop=True)
    )


def _roll_up_summary(summary_df: pd.DataFrame, period_type: str) -> pd.DataFrame:
    if summary_df.empty:
        return _empty_summary_frame()

    working = _normalize_period_columns(summary_df)
    working = _with_period_metadata(working, period_type)
    working = working.sort_values(
        by=["period_start", "period_end", "stockSymbol"],
        ascending=[True, True, True],
    )

    rolled = (
        working.groupby(
            ["period_key", "period_start", "period_end", "stockSymbol"],
            as_index=False,
        )
        .agg(
            securityName=("securityName", _last_non_empty),
            trading_days=("trading_days", "sum"),
            snapshot_count=("snapshot_count", "sum"),
            total_trades=("total_trades", "sum"),
            total_volume=("total_volume", "sum"),
            total_turnover=("total_turnover", "sum"),
            open_price=("open_price", "first"),
            close_price=("close_price", "last"),
            high_price=("high_price", "max"),
            low_price=("low_price", "min"),
            first_trade_time=("first_trade_time", "min"),
            last_trade_time=("last_trade_time", "max"),
            first_collection_time=("first_collection_time", "min"),
            last_collection_time=("last_collection_time", "max"),
            confidence_sum=("confidence_sum", "sum"),
            max_confidence=("max_confidence", "max"),
            last_confidence=("last_confidence", "last"),
            final_score_sum=("final_score_sum", "sum"),
            max_final_score=("max_final_score", "max"),
            last_final_score=("last_final_score", "last"),
            positive_signal_days=("positive_signal_days", "sum"),
            breakout_days=("breakout_days", "sum"),
            accumulation_days=("accumulation_days", "sum"),
            watch_days=("watch_days", "sum"),
            ignore_days=("ignore_days", "sum"),
            latest_signal=("latest_signal", "last"),
        )
    )

    rolled["period_type"] = period_type
    rolled["avg_price"] = _safe_divide(
        rolled["total_turnover"], rolled["total_volume"]
    )
    rolled["avg_confidence"] = _safe_divide(
        rolled["confidence_sum"], rolled["trading_days"]
    )
    rolled["avg_final_score"] = _safe_divide(
        rolled["final_score_sum"], rolled["trading_days"]
    )

    rolled = rolled[SUMMARY_COLUMNS]

    return _round_numeric_columns(
        rolled.sort_values(
            by=["period_start", "total_volume", "stockSymbol"],
            ascending=[False, False, True],
        ).reset_index(drop=True)
    )


def build_weekly_summary(daily_summary: pd.DataFrame) -> pd.DataFrame:
    return _roll_up_summary(daily_summary, "weekly")


def build_fortnightly_summary(weekly_summary: pd.DataFrame) -> pd.DataFrame:
    return _roll_up_summary(weekly_summary, "fortnightly")


def build_monthly_summary(daily_summary: pd.DataFrame) -> pd.DataFrame:
    return _roll_up_summary(daily_summary, "monthly")


def build_yearly_summary(monthly_summary: pd.DataFrame) -> pd.DataFrame:
    return _roll_up_summary(monthly_summary, "yearly")


def build_all_summaries_from_raw(raw_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    daily = build_daily_summary_from_raw(raw_df)
    weekly = build_weekly_summary(daily)
    fortnightly = build_fortnightly_summary(weekly)
    monthly = build_monthly_summary(daily)
    yearly = build_yearly_summary(monthly)

    return {
        "daily": daily,
        "weekly": weekly,
        "fortnightly": fortnightly,
        "monthly": monthly,
        "yearly": yearly,
    }


def _append_issue(
    issues: list,
    severity: str,
    scope: str,
    period_type: str,
    period_key: object,
    stock_symbol: object,
    issue_type: str,
    detail: str,
) -> None:
    issues.append(
        {
            "severity": severity,
            "scope": scope,
            "period_type": period_type,
            "period_key": "" if pd.isna(period_key) else str(period_key),
            "stockSymbol": "" if pd.isna(stock_symbol) else str(stock_symbol),
            "issue_type": issue_type,
            "detail": detail,
        }
    )


def validate_summary_frame(summary_df: pd.DataFrame, period_type: str) -> pd.DataFrame:
    if summary_df.empty:
        return _empty_validation_frame()

    working = _normalize_period_columns(summary_df)
    issues = []

    duplicate_keys = working[working.duplicated(subset=["period_key", "stockSymbol"], keep=False)]
    for _, row in duplicate_keys.iterrows():
        _append_issue(
            issues,
            "error",
            "summary",
            period_type,
            row.get("period_key"),
            row.get("stockSymbol"),
            "duplicate_summary_key",
            "More than one summary row exists for the same period_key and stockSymbol.",
        )

    for _, row in working.iterrows():
        period_key = row.get("period_key")
        stock_symbol = row.get("stockSymbol")

        if pd.isna(row.get("period_start")) or pd.isna(row.get("period_end")):
            _append_issue(
                issues,
                "error",
                "summary",
                period_type,
                period_key,
                stock_symbol,
                "missing_period_boundary",
                "Period start or end is missing.",
            )
            continue

        if row["period_end"] < row["period_start"]:
            _append_issue(
                issues,
                "error",
                "summary",
                period_type,
                period_key,
                stock_symbol,
                "invalid_period_range",
                "Period end occurs before period start.",
            )

        if pd.notna(row.get("first_collection_time")) and pd.notna(row.get("last_collection_time")):
            if row["last_collection_time"] < row["first_collection_time"]:
                _append_issue(
                    issues,
                    "error",
                    "summary",
                    period_type,
                    period_key,
                    stock_symbol,
                    "invalid_collection_window",
                    "last_collection_time occurs before first_collection_time.",
                )

        if pd.notna(row.get("first_trade_time")) and pd.notna(row.get("last_trade_time")):
            if row["last_trade_time"] < row["first_trade_time"]:
                _append_issue(
                    issues,
                    "error",
                    "summary",
                    period_type,
                    period_key,
                    stock_symbol,
                    "invalid_trade_window",
                    "last_trade_time occurs before first_trade_time.",
                )

        if pd.isna(stock_symbol) or str(stock_symbol).strip() == "":
            _append_issue(
                issues,
                "error",
                "summary",
                period_type,
                period_key,
                stock_symbol,
                "missing_symbol",
                "stockSymbol is empty.",
            )

        numeric_checks = {
            "total_trades": row.get("total_trades"),
            "total_volume": row.get("total_volume"),
            "total_turnover": row.get("total_turnover"),
            "snapshot_count": row.get("snapshot_count"),
        }
        for field_name, value in numeric_checks.items():
            if pd.notna(value) and float(value) < 0:
                _append_issue(
                    issues,
                    "error",
                    "summary",
                    period_type,
                    period_key,
                    stock_symbol,
                    "negative_metric",
                    f"{field_name} is negative.",
                )

        low_price = row.get("low_price")
        high_price = row.get("high_price")
        if pd.notna(low_price) and pd.notna(high_price) and float(high_price) < float(low_price):
            _append_issue(
                issues,
                "error",
                "summary",
                period_type,
                period_key,
                stock_symbol,
                "invalid_price_band",
                "high_price is lower than low_price.",
            )
        else:
            for field_name in ["open_price", "close_price", "avg_price"]:
                value = row.get(field_name)
                if (
                    pd.notna(value)
                    and pd.notna(low_price)
                    and pd.notna(high_price)
                    and (float(value) < float(low_price) or float(value) > float(high_price))
                ):
                    _append_issue(
                        issues,
                        "warning",
                        "summary",
                        period_type,
                        period_key,
                        stock_symbol,
                        "price_outside_band",
                        f"{field_name} falls outside the daily high/low band.",
                    )

        positive_days = float(row.get("positive_signal_days", 0))
        ignore_days = float(row.get("ignore_days", 0))
        breakout_days = float(row.get("breakout_days", 0))
        accumulation_days = float(row.get("accumulation_days", 0))
        watch_days = float(row.get("watch_days", 0))
        trading_days = float(row.get("trading_days", 0))

        if positive_days != breakout_days + accumulation_days + watch_days:
            _append_issue(
                issues,
                "warning",
                "summary",
                period_type,
                period_key,
                stock_symbol,
                "signal_count_mismatch",
                "positive signal counts do not match breakout/accumulation/watch totals.",
            )

        if trading_days != positive_days + ignore_days:
            _append_issue(
                issues,
                "warning",
                "summary",
                period_type,
                period_key,
                stock_symbol,
                "trading_day_mismatch",
                "Trading days do not match positive plus ignore days.",
            )

        if str(row.get("latest_signal", "")).upper() not in {
            "BREAKOUT",
            "ACCUMULATION",
            "WATCH",
            "IGNORE",
        }:
            _append_issue(
                issues,
                "warning",
                "summary",
                period_type,
                period_key,
                stock_symbol,
                "unknown_signal_label",
                "latest_signal contains an unexpected label.",
            )

    return pd.DataFrame(issues, columns=VALIDATION_COLUMNS)


def build_validation_issues(summaries: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    issue_frames = []

    for period_type, summary_df in summaries.items():
        frame = validate_summary_frame(summary_df, period_type)
        if not frame.empty:
            issue_frames.append(frame)

    if not issue_frames:
        return _empty_validation_frame()

    return pd.concat(issue_frames, ignore_index=True)


def build_summary_health(
    summaries: Dict[str, pd.DataFrame],
    validation_issues: pd.DataFrame,
) -> pd.DataFrame:
    health_rows = []

    for period_type, summary_df in summaries.items():
        period_issues = validation_issues[validation_issues["period_type"] == period_type]
        normalized = _normalize_period_columns(summary_df) if not summary_df.empty else summary_df

        health_rows.append(
            {
                "period_type": period_type,
                "row_count": len(summary_df),
                "period_count": summary_df["period_key"].nunique() if not summary_df.empty else 0,
                "unique_symbols": summary_df["stockSymbol"].nunique() if not summary_df.empty else 0,
                "total_trades": int(summary_df["total_trades"].sum()) if not summary_df.empty else 0,
                "total_volume": float(summary_df["total_volume"].sum()) if not summary_df.empty else 0.0,
                "issue_count": len(period_issues),
                "error_count": int((period_issues["severity"] == "error").sum()) if not period_issues.empty else 0,
                "warning_count": int((period_issues["severity"] == "warning").sum()) if not period_issues.empty else 0,
                "latest_period_start": normalized["period_start"].max() if not summary_df.empty else pd.NaT,
                "latest_period_end": normalized["period_end"].max() if not summary_df.empty else pd.NaT,
            }
        )

    return pd.DataFrame(health_rows, columns=SUMMARY_HEALTH_COLUMNS)


def build_pipeline_artifacts(folder_path: str = "data/raw/") -> Dict[str, object]:
    data_bundle = load_data_bundle(folder_path)
    raw_df = data_bundle["raw_df"]
    snapshot_index = data_bundle["snapshot_index"]
    raw_dataset_report = data_bundle["raw_dataset_report"]
    duplicate_contract_report = data_bundle["duplicate_contract_report"]
    summaries = build_all_summaries_from_raw(raw_df)
    validation_issues = build_validation_issues(summaries)
    summary_health = build_summary_health(summaries, validation_issues)

    return {
        "raw_df": raw_df,
        "snapshot_index": snapshot_index,
        "raw_dataset_report": raw_dataset_report,
        "duplicate_contract_report": duplicate_contract_report,
        "summaries": summaries,
        "validation_issues": validation_issues,
        "summary_health": summary_health,
    }


def write_summary_file(summary_df: pd.DataFrame, output_path: Path) -> Path:
    _ensure_summary_dir()
    summary_df.to_csv(output_path, index=False)
    return output_path


def write_archived_summary_file(
    summary_df: pd.DataFrame,
    period_type: str,
    run_tag: str,
) -> Path:
    _ensure_summary_dir()
    archive_dir = SUMMARY_ARCHIVE_DIR / period_type
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{period_type}_summary_{run_tag}.csv"
    summary_df.to_csv(archive_path, index=False)
    return archive_path


def write_pipeline_exports(artifacts: Dict[str, object]) -> Dict[str, Path]:
    written_files: Dict[str, Path] = {}
    summaries = artifacts.get("summaries", {})

    for period_type, output_path in SUMMARY_FILES.items():
        written_files[period_type] = write_summary_file(
            summaries.get(period_type, _empty_summary_frame()),
            output_path,
        )

    written_files["pipeline_report"] = write_summary_file(
        artifacts.get("raw_dataset_report", pd.DataFrame()),
        PIPELINE_REPORT_FILE,
    )
    written_files["summary_health"] = write_summary_file(
        artifacts.get("summary_health", pd.DataFrame()),
        SUMMARY_HEALTH_FILE,
    )
    written_files["validation_issues"] = write_summary_file(
        artifacts.get("validation_issues", pd.DataFrame()),
        VALIDATION_ISSUES_FILE,
    )
    written_files["duplicate_contract_report"] = write_summary_file(
        artifacts.get("duplicate_contract_report", pd.DataFrame()),
        DUPLICATE_CONTRACT_REPORT_FILE,
    )

    return written_files


def write_selected_summary_exports(
    artifacts: Dict[str, object],
    period_types: list[str],
    run_tag: str,
) -> Dict[str, Path]:
    written_files: Dict[str, Path] = {}
    summaries = artifacts.get("summaries", {})

    for period_type in period_types:
        summary_df = summaries.get(period_type, _empty_summary_frame())
        canonical_path = SUMMARY_FILES[period_type]
        written_files[period_type] = write_summary_file(summary_df, canonical_path)
        written_files[f"{period_type}_archive"] = write_archived_summary_file(
            summary_df,
            period_type,
            run_tag,
        )

    return written_files


def build_all_summaries(folder_path: str = "data/raw/") -> Dict[str, pd.DataFrame]:
    return build_pipeline_artifacts(folder_path)["summaries"]


def write_all_summaries(folder_path: str = "data/raw/") -> Dict[str, Path]:
    artifacts = build_pipeline_artifacts(folder_path)
    return write_pipeline_exports(artifacts)
