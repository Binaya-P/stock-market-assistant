from portfolio.portfolio_manager import *

CONFIDENCE_ADD_THRESHOLD = 15
CONFIDENCE_EXIT_THRESHOLD = 20


def process_signals(signal_df):
    portfolio = load_portfolio()

    for _, row in signal_df.iterrows():
        symbol = row["stock"]
        confidence = row["confidence"]
        signal = row["system_signal"]
        price = row["avg_price"]

        existing = portfolio[portfolio["symbol"] == symbol]

        # 🟢 NEW STOCK
        if existing.empty:
            if signal in ["ACCUMULATION"]:
                print(f"NEW BUY: {symbol}")
                add_position(symbol, quantity=10, price=price, confidence=confidence)

        # 🔵 EXISTING STOCK
        else:
            old_conf = existing.iloc[0]["confidence"]

            # upgrade
            if confidence - old_conf >= CONFIDENCE_ADD_THRESHOLD:
                print(f"UPGRADE: {symbol}")

            # exit
            elif old_conf - confidence >= CONFIDENCE_EXIT_THRESHOLD:
                print(f"EXIT: {symbol}")
                remove_position(symbol)

            # always update confidence
            update_confidence(symbol, confidence)