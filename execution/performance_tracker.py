import json
from datetime import datetime
from pathlib import Path


STATE_FILE = Path("data/state/virtual_trader_state.json")
PERF_FILE = Path("data/state/virtual_performance.json")


# -----------------------------
# LOAD / SAVE
# -----------------------------
def load_state():
    if not STATE_FILE.exists():
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def load_perf():
    if not PERF_FILE.exists():
        return {
            "initial_capital": 500000,
            "realized_pnl": 0,
            "trade_count": 0,
            "wins": 0,
            "losses": 0,
            "equity_curve": []
        }
    with open(PERF_FILE, "r") as f:
        return json.load(f)


def save_perf(perf):
    PERF_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERF_FILE, "w") as f:
        json.dump(perf, f, indent=2)


# -----------------------------
# CORE METRICS
# -----------------------------
def calculate_unrealized(state):
    total = 0
    for pos in state["positions"].values():
        total += pos["value"]
    return total


def calculate_equity(state):
    return state["cash"] + calculate_unrealized(state)


# -----------------------------
# TRADE LOG PROCESSING
# -----------------------------
def update_trade_stats(perf, state):
    logs = state.get("trade_log", [])

    for trade in logs:
        if trade.get("processed"):
            continue

        if trade["action"] == "SELL":
            pnl = trade.get("pnl", 0)

            perf["trade_count"] += 1
            perf["realized_pnl"] += pnl

            if pnl > 0:
                perf["wins"] += 1
            else:
                perf["losses"] += 1

        trade["processed"] = True


# -----------------------------
# MAIN ENTRY
# -----------------------------
def update_performance():

    state = load_state()
    if not state:
        return

    perf = load_perf()

    # update trades
    update_trade_stats(perf, state)

    # equity snapshot
    equity = calculate_equity(state)

    perf["equity_curve"].append({
        "time": str(datetime.now()),
        "equity": equity
    })

    save_perf(perf)

    # persist updated trade log flags
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    print("Performance updated.")