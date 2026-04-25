import pandas as pd

from execution.wishlist_engine import update_wishlist

REQUIRED_COLUMNS = {"stock", "confidence", "system_signal", "avg_price"}

# thresholds
STRONG_THRESHOLD = 80
SPECULATIVE_THRESHOLD = 65
EXIT_THRESHOLD = 45


def process_signals(signal_df: pd.DataFrame) -> pd.DataFrame:
    if signal_df.empty:
        return pd.DataFrame(columns=["symbol", "action", "confidence", "signal"])

    missing = REQUIRED_COLUMNS.difference(signal_df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    actions = []
    wishlist_entries = []

    for _, row in signal_df.iterrows():
        symbol = str(row["stock"]).strip().upper()
        confidence = float(row["confidence"])
        signal = str(row["system_signal"]).strip().upper()
        price = float(row["avg_price"])

        action = "SKIP"

        # --- USER SUGGESTIONS ---
        if signal in {"ACCUMULATION", "BREAKOUT"}:
            if confidence >= STRONG_THRESHOLD:
                print(f"SUGGEST ADD: {symbol}")
                action = "ADD"

                # also goes to wishlist
                wishlist_entries.append({
                    "symbol": symbol,
                    "confidence": confidence,
                    "price": price,
                    "type": "STRONG",
                    "signal": signal
                })

            elif confidence >= SPECULATIVE_THRESHOLD:
                print(f"WISHLIST (SPECULATIVE): {symbol}")
                action = "WISHLIST_SPECULATIVE"

                wishlist_entries.append({
                    "symbol": symbol,
                    "confidence": confidence,
                    "price": price,
                    "type": "SPECULATIVE",
                    "signal": signal
                })

            else:
                action = "HOLD"

        elif signal == "WATCH":
            if confidence < EXIT_THRESHOLD:
                print(f"SUGGEST REDUCE: {symbol}")
                action = "REDUCE"
            else:
                action = "HOLD"

        elif signal == "IGNORE":
            print(f"SUGGEST EXIT: {symbol}")
            action = "EXIT"

        actions.append({
            "symbol": symbol,
            "action": action,
            "confidence": round(confidence, 2),
            "signal": signal
        })

    # update wishlist
    if wishlist_entries:
        update_wishlist(wishlist_entries)

    return pd.DataFrame(actions)