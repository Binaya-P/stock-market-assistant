import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


STATE_FILE = Path("data/state/virtual_trader_state.json")
WISHLIST_FILE = Path("data/state/wishlist.csv")


# -----------------------------
# CONFIG
# -----------------------------
def load_config():
    with open("config/system_config.json", "r") as f:
        return json.load(f)


# -----------------------------
# STATE
# -----------------------------
def load_state():
    if not STATE_FILE.exists():
        return {
            "cash": 500000,
            "positions": {},
            "pending_settlements": [],
            "trade_log": []
        }
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# -----------------------------
# MARKET HOURS
# -----------------------------
def is_market_open():
    cfg = load_config()
    now = datetime.now()
    return cfg["market"]["start_hour"] <= now.hour < cfg["market"]["end_hour"]


# -----------------------------
# WISHLIST
# -----------------------------
def load_wishlist():
    if not WISHLIST_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(WISHLIST_FILE)


# -----------------------------
# ALLOCATION LOGIC
# -----------------------------
def confidence_to_target(confidence, max_pct):
    if confidence >= 95:
        return max_pct
    elif confidence >= 90:
        return max_pct * 0.75
    elif confidence >= 80:
        return max_pct * 0.5
    elif confidence >= 70:
        return max_pct * 0.3
    else:
        return 0


# -----------------------------
# SETTLEMENT HANDLING (T+3)
# -----------------------------
def process_settlements(state):
    today = datetime.now().date()
    remaining = []

    for s in state["pending_settlements"]:
        release_date = datetime.fromisoformat(s["release_date"]).date()
        if today >= release_date:
            state["cash"] += s["amount"]
        else:
            remaining.append(s)

    state["pending_settlements"] = remaining


# -----------------------------
# CORE ENGINE
# -----------------------------
def run_virtual_trader():

    cfg = load_config()["virtual_trader"]

    if not cfg["enabled"]:
        return

    if not is_market_open():
        print("Market closed → skipping virtual trader")
        return

    state = load_state()
    wishlist = load_wishlist()

    process_settlements(state)

    total_equity = state["cash"] + sum(
        pos["value"] for pos in state["positions"].values()
    )

    deployable_cash = state["cash"] * (1 - cfg["cash_reserve_pct"])

    for _, row in wishlist.iterrows():

        symbol = row["symbol"]
        confidence = row["confidence"]
        price = row["price"]

        target_pct = confidence_to_target(confidence, cfg["max_position_pct"])
        target_value = total_equity * target_pct

        current = state["positions"].get(symbol, {"value": 0})
        current_value = current["value"]

        diff = target_value - current_value

        # Minimum threshold check
        if diff / total_equity < cfg["min_add_pct"]:
            continue

        if diff > 0:
            # BUY
            if deployable_cash <= 0:
                continue

            invest = min(diff, deployable_cash)
            qty = invest / price

            state["cash"] -= invest
            deployable_cash -= invest

            new_value = current_value + invest

            state["positions"][symbol] = {
                "quantity": current.get("quantity", 0) + qty,
                "value": new_value,
                "avg_price": price
            }

            state["trade_log"].append({
                "time": str(datetime.now()),
                "symbol": symbol,
                "action": "BUY",
                "amount": invest
            })

        elif diff < 0:
            # SELL
            sell_value = abs(diff)

            pos = state["positions"].get(symbol)
            if not pos:
                continue

            sell_value = min(sell_value, pos["value"])

            pos["value"] -= sell_value

            if pos["value"] <= 0:
                del state["positions"][symbol]

            # T+3 settlement
            state["pending_settlements"].append({
                "amount": sell_value,
                "release_date": str(datetime.now() + timedelta(days=3))
            })

            state["trade_log"].append({
                "time": str(datetime.now()),
                "symbol": symbol,
                "action": "SELL",
                "amount": sell_value
            })

    save_state(state)
    print("Virtual trader executed.")