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
            "equity_curve": [],
            "last_snapshot_time": None
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
    return sum(pos.get("value", 0) for pos in state.get("positions", {}).values())


def calculate_equity(state):
    return state.get("cash", 0) + calculate_unrealized(state)


def calculate_return_pct(equity, initial_capital):
    if initial_capital == 0:
        return 0
    return round(((equity - initial_capital) / initial_capital) * 100, 2)


# -----------------------------
# TRADE LOG PROCESSING
# -----------------------------
def update_trade_stats(perf, state):
    logs = state.get("trade_log", [])

    for trade in logs:
        if trade.get("processed"):
            continue

        if trade.get("action") == "SELL":
            pnl = trade.get("pnl", 0)

            perf["trade_count"] += 1
            perf["realized_pnl"] += pnl

            if pnl > 0:
                perf["wins"] += 1
            else:
                perf["losses"] += 1

        trade["processed"] = True


# -----------------------------
# SNAPSHOT CONTROL
# -----------------------------
def should_take_snapshot(perf):
    now = datetime.now()

    if perf.get("last_snapshot_time") is None:
        return True

    last = datetime.fromisoformat(perf["last_snapshot_time"])

    # prevent duplicate within same minute
    return (now - last).seconds >= 60


# -----------------------------
# MAIN ENTRY
# -----------------------------
def update_performance():

    state = load_state()
    if not state:
        return

    perf = load_perf()

    # update trade stats
    update_trade_stats(perf, state)

    equity = calculate_equity(state)
    return_pct = calculate_return_pct(equity, perf["initial_capital"])

    # snapshot control
    if should_take_snapshot(perf):
        perf["equity_curve"].append({
            "time": str(datetime.now()),
            "equity": equity,
            "return_pct": return_pct
        })
        perf["last_snapshot_time"] = str(datetime.now())

    # derived metrics
    total_trades = perf["trade_count"]
    wins = perf["wins"]

    perf["win_rate"] = round((wins / total_trades) * 100, 2) if total_trades > 0 else 0

    save_perf(perf)

    # persist updated trade flags
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    print("Virtual performance updated.")