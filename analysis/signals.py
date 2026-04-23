from pathlib import Path
from typing import Optional

import pandas as pd

from analysis.dataset_builder import build_daily_summary_from_raw


SIGNAL_COLUMNS = [
    "period_type",
    "period_key",
    "stock",
    "avg_price",
    "volume",
    "trades",
    "liquidity_score",
    "quality_score",
    "momentum_score",
    "persistence_score",
    "close_strength",
    "intraday_return",
    "confidence",
    "final_score",
    "rank",
    "system_signal",
]

SUMMARY_REQUIRED_COLUMNS = {
    "period_type",
    "period_key",
    "stockSymbol",
    "avg_price",
    "total_volume",
    "total_trades",
    "open_price",
    "close_price",
    "high_price",
    "low_price",
    "avg_confidence",
    "avg_final_score",
    "positive_signal_days",
    "breakout_days",
    "accumulation_days",
    "trading_days",
}


def _normalize(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=float)

    min_value = series.min()
    max_value = series.max()

    if pd.isna(min_value) or pd.isna(max_value) or max_value <= min_value:
        return pd.Series(0.5, index=series.index)

    return (series - min_value) / (max_value - min_value)


def _rank_percentile(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=float)

    ranked = series.rank(method="average", pct=True)
    return ranked.fillna(0.0)


def _is_summary_frame(df: pd.DataFrame) -> bool:
    return SUMMARY_REQUIRED_COLUMNS.issubset(df.columns)


def _prepare_summary_source(df: pd.DataFrame, period_key: Optional[str] = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=SIGNAL_COLUMNS)

    if _is_summary_frame(df):
        summary_df = df.copy()
    else:
        summary_df = build_daily_summary_from_raw(df)

    if summary_df.empty:
        return pd.DataFrame(columns=SIGNAL_COLUMNS)

    summary_df = summary_df.copy()
    summary_df["period_start"] = pd.to_datetime(summary_df["period_start"], errors="coerce")

    if period_key is None:
        latest_period_start = summary_df["period_start"].max()
        summary_df = summary_df[summary_df["period_start"] == latest_period_start].copy()
    else:
        summary_df = summary_df[summary_df["period_key"].astype(str) == str(period_key)].copy()

    return summary_df.reset_index(drop=True)


def _classify_signal(row: pd.Series, breakout_rank_limit: int, accumulation_rank_limit: int, watch_rank_limit: int) -> str:
    if (
        row["final_score"] >= 78
        and row["rank"] <= breakout_rank_limit
        and row["close_strength"] >= 0.68
        and row["intraday_return"] >= 0
        and row["liquidity_score"] >= 60
    ):
        return "BREAKOUT"

    if (
        row["final_score"] >= 62
        and row["rank"] <= accumulation_rank_limit
        and row["quality_score"] >= 55
    ):
        return "ACCUMULATION"

    if (
        row["final_score"] >= 50
        and row["rank"] <= watch_rank_limit
    ):
        return "WATCH"

    return "IGNORE"


def generate_signals(
    df: pd.DataFrame,
    min_volume: int = 20000,
    min_trades: int = 100,
    period_key: Optional[str] = None,
) -> pd.DataFrame:
    summary_df = _prepare_summary_source(df, period_key=period_key)

    if summary_df.empty:
        return pd.DataFrame(columns=SIGNAL_COLUMNS)

    working = summary_df.copy()
    working = working[
        (pd.to_numeric(working["total_volume"], errors="coerce").fillna(0) >= min_volume)
        & (pd.to_numeric(working["total_trades"], errors="coerce").fillna(0) >= min_trades)
    ].copy()

    if working.empty:
        return pd.DataFrame(columns=SIGNAL_COLUMNS)

    working["intraday_return"] = (
        (working["close_price"] - working["open_price"])
        / working["open_price"].replace(0, pd.NA)
    ).fillna(0.0)
    price_span = (working["high_price"] - working["low_price"]).clip(lower=0)
    working["close_strength"] = (
        (working["close_price"] - working["low_price"])
        / price_span.replace(0, pd.NA)
    ).clip(lower=0, upper=1).fillna(0.5)
    working["range_pct"] = (
        price_span / working["avg_price"].replace(0, pd.NA)
    ).fillna(0.0)

    positive_signal_ratio = (
        working["positive_signal_days"] / working["trading_days"].replace(0, pd.NA)
    ).fillna(0.0)
    breakout_ratio = (
        working["breakout_days"] / working["trading_days"].replace(0, pd.NA)
    ).fillna(0.0)
    accumulation_ratio = (
        working["accumulation_days"] / working["trading_days"].replace(0, pd.NA)
    ).fillna(0.0)

    volume_rank = _rank_percentile(working["total_volume"])
    trade_rank = _rank_percentile(working["total_trades"])
    turnover_rank = _rank_percentile(working["total_turnover"])
    confidence_rank = _rank_percentile(working["avg_confidence"])
    final_rank = _rank_percentile(working["avg_final_score"])
    return_rank = _rank_percentile(working["intraday_return"].clip(lower=-0.15, upper=0.15))
    range_rank = _rank_percentile(working["range_pct"])

    working["liquidity_score"] = (
        volume_rank * 0.6 + trade_rank * 0.4
    ) * 100

    working["quality_score"] = (
        final_rank * 0.45 + confidence_rank * 0.35 + turnover_rank * 0.20
    ) * 100

    working["momentum_score"] = (
        working["close_strength"] * 0.45 + return_rank * 0.35 + range_rank * 0.20
    ) * 100

    working["persistence_score"] = (
        positive_signal_ratio * 0.5 + breakout_ratio * 0.3 + accumulation_ratio * 0.2
    ) * 100

    working["confidence"] = (
        working["quality_score"] * 0.5
        + working["momentum_score"] * 0.3
        + working["persistence_score"] * 0.2
    )

    working["final_score"] = (
        working["liquidity_score"] * 0.35
        + working["quality_score"] * 0.30
        + working["momentum_score"] * 0.20
        + working["persistence_score"] * 0.15
    )

    working = working.sort_values(
        by=["final_score", "quality_score", "liquidity_score"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    working["rank"] = working.index + 1

    total_rows = len(working)
    breakout_rank_limit = max(3, int(total_rows * 0.05))
    accumulation_rank_limit = max(10, int(total_rows * 0.22))
    watch_rank_limit = max(25, int(total_rows * 0.45))

    working["system_signal"] = working.apply(
        _classify_signal,
        axis=1,
        breakout_rank_limit=breakout_rank_limit,
        accumulation_rank_limit=accumulation_rank_limit,
        watch_rank_limit=watch_rank_limit,
    )

    result = pd.DataFrame(
        {
            "period_type": working["period_type"],
            "period_key": working["period_key"],
            "stock": working["stockSymbol"],
            "avg_price": working["avg_price"].round(2),
            "volume": working["total_volume"],
            "trades": working["total_trades"],
            "liquidity_score": working["liquidity_score"].round(2),
            "quality_score": working["quality_score"].round(2),
            "momentum_score": working["momentum_score"].round(2),
            "persistence_score": working["persistence_score"].round(2),
            "close_strength": working["close_strength"].round(4),
            "intraday_return": working["intraday_return"].round(4),
            "confidence": working["confidence"].round(2),
            "final_score": working["final_score"].round(2),
            "rank": working["rank"],
            "system_signal": working["system_signal"],
        }
    )

    return result.sort_values(
        by=["final_score", "confidence", "volume"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
