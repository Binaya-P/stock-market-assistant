import pandas as pd

from portfolio.portfolio_manager import (
    add_position,
    load_portfolio,
    remove_position,
    update_position,
)


CONFIDENCE_ADD_THRESHOLD = 15
CONFIDENCE_EXIT_THRESHOLD = 20

REQUIRED_SIGNAL_COLUMNS = {"stock", "confidence", "system_signal", "avg_price"}


def process_signals(signal_df: pd.DataFrame) -> pd.DataFrame:
    if signal_df.empty:
        print("[INFO] No signals matched the configured filters.")
        return pd.DataFrame(columns=["symbol", "action", "confidence", "signal"])

    missing = REQUIRED_SIGNAL_COLUMNS.difference(signal_df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Signal dataframe is missing required columns: {missing_list}")

    portfolio = load_portfolio()
    actions: list[dict[str, object]] = []

    for _, row in signal_df.iterrows():
        symbol = str(row["stock"]).strip().upper()
        confidence = float(row["confidence"])
        signal = str(row["system_signal"]).strip().upper()
        price = float(row["avg_price"])

        existing = portfolio[portfolio["symbol"] == symbol]

        if existing.empty:
            if signal in {"ACCUMULATION", "BREAKOUT"}:
                print(f"NEW BUY: {symbol}")
                add_position(
                    symbol=symbol,
                    quantity=10,
                    price=price,
                    confidence=confidence,
                    signal_type=signal,
                )
                action = "BUY"
            else:
                action = "SKIP"

        else:
            old_confidence = float(existing.iloc[0]["confidence"])

            if signal == "IGNORE" or old_confidence - confidence >= CONFIDENCE_EXIT_THRESHOLD:
                print(f"EXIT: {symbol}")
                remove_position(symbol)
                action = "EXIT"
            elif confidence - old_confidence >= CONFIDENCE_ADD_THRESHOLD:
                print(f"UPGRADE: {symbol}")
                update_position(
                    symbol,
                    price=price,
                    confidence=confidence,
                    signal_type=signal,
                )
                action = "UPGRADE"
            else:
                update_position(
                    symbol,
                    price=price,
                    confidence=confidence,
                    signal_type=signal,
                )
                action = "HOLD"

        actions.append(
            {
                "symbol": symbol,
                "action": action,
                "confidence": round(confidence, 2),
                "signal": signal,
            }
        )
        portfolio = load_portfolio()

    return pd.DataFrame(actions)
