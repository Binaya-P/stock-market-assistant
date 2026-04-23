from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

PORTFOLIO_FILE = Path("data/state/portfolio.csv")

PORTFOLIO_COLUMNS = [
    "symbol",
    "quantity",
    "avg_price",
    "current_price",
    "confidence",
    "signal_type",
    "last_updated",
]


# -------------------------------
# INTERNAL HELPERS
# -------------------------------
def _empty_portfolio() -> pd.DataFrame:
    return pd.DataFrame(columns=PORTFOLIO_COLUMNS)


def _ensure_state_dir():
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)


def _align_schema(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    defaults = {
        "symbol": "",
        "quantity": 0.0,
        "avg_price": 0.0,
        "current_price": 0.0,
        "confidence": 0.0,
        "signal_type": "UNKNOWN",
        "last_updated": "",
    }

    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val

    df = df[PORTFOLIO_COLUMNS]

    df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()

    for col in ["quantity", "avg_price", "current_price", "confidence"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["signal_type"] = df["signal_type"].astype(str).str.upper()
    df["last_updated"] = df["last_updated"].astype(str)

    return df


# -------------------------------
# CORE FUNCTIONS
# -------------------------------
def load_portfolio() -> pd.DataFrame:
    if not PORTFOLIO_FILE.exists():
        return _empty_portfolio()

    df = pd.read_csv(PORTFOLIO_FILE)
    return _align_schema(df)


def save_portfolio(df: pd.DataFrame):
    _ensure_state_dir()
    _align_schema(df).to_csv(PORTFOLIO_FILE, index=False)


# -------------------------------
# POSITION MANAGEMENT
# -------------------------------
def add_position(symbol, quantity, price, confidence, signal_type="ACCUMULATION"):
    df = load_portfolio()
    symbol = symbol.upper().strip()
    now = datetime.now().isoformat(sep=" ", timespec="seconds")

    existing = df["symbol"] == symbol

    if existing.any():
        idx = df.index[existing][0]

        old_qty = df.at[idx, "quantity"]
        old_price = df.at[idx, "avg_price"]

        new_qty = old_qty + quantity

        if new_qty <= 0:
            remove_position(symbol)
            return

        new_avg = ((old_qty * old_price) + (quantity * price)) / new_qty

        df.at[idx, "quantity"] = new_qty
        df.at[idx, "avg_price"] = round(new_avg, 2)
        df.at[idx, "current_price"] = price
        df.at[idx, "confidence"] = confidence
        df.at[idx, "signal_type"] = signal_type
        df.at[idx, "last_updated"] = now

    else:
        new_row = {
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": price,
            "current_price": price,
            "confidence": confidence,
            "signal_type": signal_type,
            "last_updated": now,
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    save_portfolio(df)


def update_position(symbol, price=None, confidence=None, signal_type=None):
    df = load_portfolio()
    symbol = symbol.upper().strip()

    existing = df["symbol"] == symbol
    if not existing.any():
        return

    idx = df.index[existing][0]

    if price is not None:
        df.at[idx, "current_price"] = price

    if confidence is not None:
        df.at[idx, "confidence"] = confidence

    if signal_type is not None:
        df.at[idx, "signal_type"] = signal_type

    df.at[idx, "last_updated"] = datetime.now().isoformat(
        sep=" ", timespec="seconds"
    )

    save_portfolio(df)


def remove_position(symbol):
    df = load_portfolio()
    symbol = symbol.upper().strip()
    df = df[df["symbol"] != symbol]
    save_portfolio(df)


# -------------------------------
# FUTURE: CAPITAL ALLOCATION
# -------------------------------
def allocate_capital(signals_df, total_capital=100):
    buy_df = signals_df[
        signals_df["system_signal"].isin(["ACCUMULATION", "BREAKOUT"])
    ]

    if buy_df.empty:
        return []

    deployable = total_capital * 0.75
    total_conf = buy_df["confidence"].sum()

    allocations = []

    for _, row in buy_df.iterrows():
        weight = row["confidence"] / total_conf
        allocation = weight * deployable

        allocation = min(allocation, total_capital * 0.20)

        allocations.append(
            {
                "symbol": row["stock"],
                "allocation_percent": round(allocation, 2),
                "confidence": row["confidence"],
            }
        )

    return allocations