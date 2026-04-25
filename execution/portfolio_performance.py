import json
from pathlib import Path
import pandas as pd

PORTFOLIO_FILE = Path("data/state/portfolio.csv")
PERF_FILE = Path("data/state/portfolio_performance.json")


def load_portfolio():
    if not PORTFOLIO_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(PORTFOLIO_FILE)


def calculate_performance():

    df = load_portfolio()

    if df.empty:
        return

    df["invested"] = df["quantity"] * df["avg_price"]
    df["current_value"] = df["quantity"] * df["current_price"]

    total_invested = df["invested"].sum()
    total_value = df["current_value"].sum()

    pnl = total_value - total_invested

    return_pct = (pnl / total_invested * 100) if total_invested > 0 else 0

    perf = {
        "total_invested": round(total_invested, 2),
        "current_value": round(total_value, 2),
        "pnl": round(pnl, 2),
        "return_pct": round(return_pct, 2)
    }

    PERF_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERF_FILE, "w") as f:
        json.dump(perf, f, indent=2)

    print("Portfolio performance updated.")
    return perf