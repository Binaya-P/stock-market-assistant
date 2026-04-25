from datetime import datetime
from pathlib import Path
import pandas as pd

WISHLIST_FILE = Path("data/state/wishlist.csv")

COLUMNS = [
    "symbol",
    "confidence",
    "price",
    "type",
    "last_signal",
    "first_seen",
    "last_updated",
    "status",
    "max_confidence",
]


def load_wishlist():
    if not WISHLIST_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)

    df = pd.read_csv(WISHLIST_FILE)

    # align schema if old file exists
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[COLUMNS]


def save_wishlist(df):
    WISHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(WISHLIST_FILE, index=False)


def update_wishlist(entries: list[dict]):
    df = load_wishlist()
    now = datetime.now().isoformat(sep=" ", timespec="seconds")

    for entry in entries:
        symbol = entry["symbol"]

        existing = df[df["symbol"] == symbol]

        if existing.empty:
            new_row = {
                "symbol": symbol,
                "confidence": entry["confidence"],
                "price": entry["price"],
                "type": entry["type"],
                "last_signal": entry["signal"],
                "first_seen": now,
                "last_updated": now,
                "status": "ACTIVE",
                "max_confidence": entry["confidence"],
            }

            new_df = pd.DataFrame([new_row])

            if df.empty:
                df = new_df
            else:
                df = pd.concat([df, new_df], ignore_index=True)

        else:
            idx = existing.index[0]

            df.at[idx, "confidence"] = entry["confidence"]
            df.at[idx, "price"] = entry["price"]
            df.at[idx, "type"] = entry["type"]
            df.at[idx, "last_signal"] = entry["signal"]
            df.at[idx, "last_updated"] = now
            df.at[idx, "status"] = "ACTIVE"
            df.at[idx, "max_confidence"] = max(
            df.at[idx, "max_confidence"],
            entry["confidence"]
            )

    save_wishlist(df)