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


def _empty_portfolio() -> pd.DataFrame:
    return pd.DataFrame(columns=PORTFOLIO_COLUMNS)


def _ensure_state_dir() -> None:
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)


def _align_portfolio_schema(df: pd.DataFrame) -> pd.DataFrame:
    aligned = df.copy()

    defaults = {
        "symbol": "",
        "quantity": 0.0,
        "avg_price": 0.0,
        "current_price": 0.0,
        "confidence": 0.0,
        "signal_type": "UNKNOWN",
        "last_updated": "",
    }

    for column, default_value in defaults.items():
        if column not in aligned.columns:
            aligned[column] = default_value

    aligned = aligned[PORTFOLIO_COLUMNS]

    aligned["symbol"] = aligned["symbol"].astype(str).str.strip().str.upper()

    for column in ["quantity", "avg_price", "current_price", "confidence"]:
        aligned[column] = pd.to_numeric(aligned[column], errors="coerce").fillna(0.0)

    aligned["signal_type"] = aligned["signal_type"].astype(str).str.strip().str.upper()
    aligned["last_updated"] = aligned["last_updated"].astype(str)

    return aligned


def load_portfolio() -> pd.DataFrame:
    if not PORTFOLIO_FILE.exists():
        return _empty_portfolio()

    portfolio = pd.read_csv(PORTFOLIO_FILE)
    return _align_portfolio_schema(portfolio)


def save_portfolio(df: pd.DataFrame) -> None:
    _ensure_state_dir()
    _align_portfolio_schema(df).to_csv(PORTFOLIO_FILE, index=False)


def add_position(
    symbol: str,
    quantity: float,
    price: float,
    confidence: float,
    signal_type: str = "ACCUMULATION",
) -> None:
    portfolio = load_portfolio()
    symbol = symbol.strip().upper()
    timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")

    existing = portfolio["symbol"] == symbol

    if existing.any():
        row_index = portfolio.index[existing][0]
        current_quantity = float(portfolio.at[row_index, "quantity"])
        current_avg_price = float(portfolio.at[row_index, "avg_price"])
        new_quantity = current_quantity + quantity

        if new_quantity <= 0:
            remove_position(symbol)
            return

        weighted_avg_price = (
            (current_quantity * current_avg_price) + (quantity * price)
        ) / new_quantity

        portfolio.at[row_index, "quantity"] = new_quantity
        portfolio.at[row_index, "avg_price"] = round(weighted_avg_price, 2)
        portfolio.at[row_index, "current_price"] = price
        portfolio.at[row_index, "confidence"] = confidence
        portfolio.at[row_index, "signal_type"] = signal_type
        portfolio.at[row_index, "last_updated"] = timestamp
    else:
        new_row = {
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": price,
            "current_price": price,
            "confidence": confidence,
            "signal_type": signal_type,
            "last_updated": timestamp,
        }
        portfolio = pd.concat([portfolio, pd.DataFrame([new_row])], ignore_index=True)

    save_portfolio(portfolio)


def update_position(
    symbol: str,
    price: Optional[float] = None,
    confidence: Optional[float] = None,
    signal_type: Optional[str] = None,
) -> None:
    portfolio = load_portfolio()
    symbol = symbol.strip().upper()
    existing = portfolio["symbol"] == symbol

    if not existing.any():
        return

    row_index = portfolio.index[existing][0]

    if price is not None:
        portfolio.at[row_index, "current_price"] = price
    if confidence is not None:
        portfolio.at[row_index, "confidence"] = confidence
    if signal_type is not None:
        portfolio.at[row_index, "signal_type"] = signal_type

    portfolio.at[row_index, "last_updated"] = datetime.now().isoformat(
        sep=" ", timespec="seconds"
    )

    save_portfolio(portfolio)


def update_confidence(symbol: str, confidence: float) -> None:
    update_position(symbol, confidence=confidence)


def remove_position(symbol: str) -> None:
    portfolio = load_portfolio()
    symbol = symbol.strip().upper()
    portfolio = portfolio[portfolio["symbol"] != symbol]
    save_portfolio(portfolio)
