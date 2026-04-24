import pandas as pd
from pathlib import Path
from datetime import datetime

from portfolio.portfolio_manager import load_portfolio

# -------------------------------
# CONFIG
# -------------------------------
CONFIDENCE_ADD_THRESHOLD = 15
CONFIDENCE_EXIT_THRESHOLD = 20

MIN_CONFIDENCE_BUY = 70
MIN_FINAL_SCORE_BUY = 75

REQUIRED_SIGNAL_COLUMNS = {
    "stock",
    "confidence",
    "system_signal",
    "avg_price",
    "final_score",
}

WISHLIST_FILE = Path("data/state/wishlist.csv")


# -------------------------------
# WISHLIST
# -------------------------------
def load_wishlist():
    if not WISHLIST_FILE.exists():
        return pd.DataFrame(columns=["symbol", "confidence", "signal", "price", "added_at"])
    return pd.read_csv(WISHLIST_FILE)


def save_wishlist(df):
    WISHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(WISHLIST_FILE, index=False)


def add_to_wishlist(symbol, confidence, signal, price):
    df = load_wishlist()
    symbol = symbol.upper().strip()

    if symbol in df["symbol"].values:
        return

    new_row = {
        "symbol": symbol,
        "confidence": confidence,
        "signal": signal,
        "price": price,
        "added_at": datetime.now().isoformat(timespec="seconds"),
    }

    new_df = pd.DataFrame([new_row])

    if df.empty:
        df = new_df
    else:
        df = pd.concat([df, new_df], ignore_index=True)
    save_wishlist(df)


# -------------------------------
# MAIN ENGINE (NO EXECUTION)
# -------------------------------
def process_signals(signal_df: pd.DataFrame) -> pd.DataFrame:
    if signal_df.empty:
        print("[INFO] No signals available.")
        return pd.DataFrame(columns=["symbol", "action", "confidence", "signal"])

    missing = REQUIRED_SIGNAL_COLUMNS.difference(signal_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    portfolio = load_portfolio()
    actions = []

    for _, row in signal_df.iterrows():
        symbol = str(row["stock"]).strip().upper()
        confidence = float(row["confidence"])
        signal = str(row["system_signal"]).strip().upper()
        price = float(row["avg_price"])
        final_score = float(row["final_score"])

        existing = portfolio[portfolio["symbol"] == symbol]

        # -------------------------------
        # NOT IN PORTFOLIO → WISHLIST
        # -------------------------------
        if existing.empty:
            if signal in {"ACCUMULATION", "BREAKOUT"}:

                if confidence >= 75:
                    tier = "STRONG"
                elif confidence >= 60:
                    tier = "SPECULATIVE"
                else:
                    tier = None

                if tier:
                    print(f"WISHLIST ({tier}): {symbol}")

                    add_to_wishlist(
                        symbol=symbol,
                        confidence=confidence,
                        signal=f"{signal}_{tier}",
                        price=price,
                    )

                    action = f"WISHLIST_{tier}"
                else:
                    action = "SKIP"
            else:
                action = "SKIP"

        # -------------------------------
        # IN PORTFOLIO → SUGGESTIONS ONLY
        # -------------------------------
        else:
            old_conf = float(existing.iloc[0]["confidence"])

            # ❌ EXIT SUGGESTION
            if signal == "IGNORE" or (old_conf - confidence >= CONFIDENCE_EXIT_THRESHOLD):
                print(f"SUGGEST EXIT: {symbol}")
                action = "EXIT"

            # ⚠️ WEAK SIGNAL
            elif confidence < 50:
                print(f"SUGGEST REDUCE: {symbol}")
                action = "REDUCE"

            # 🔼 UPGRADE SUGGESTION
            elif confidence - old_conf >= CONFIDENCE_ADD_THRESHOLD:
                print(f"SUGGEST ADD: {symbol}")
                action = "ADD"

            # 🔄 HOLD
            else:
                action = "HOLD"

        actions.append(
            {
                "symbol": symbol,
                "action": action,
                "confidence": round(confidence, 2),
                "signal": signal,
            }
        )

    return pd.DataFrame(actions)