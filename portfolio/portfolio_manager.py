import pandas as pd
import os
from datetime import datetime

PORTFOLIO_FILE = "data/state/portfolio.csv"


def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return pd.DataFrame(columns=[
            "symbol", "quantity", "avg_price", "confidence", "last_updated"
        ])
    return pd.read_csv(PORTFOLIO_FILE)


def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)


def add_position(symbol, quantity, price, confidence):
    df = load_portfolio()

    new_row = {
        "symbol": symbol,
        "quantity": quantity,
        "avg_price": price,
        "confidence": confidence,
        "last_updated": datetime.now()
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_portfolio(df)


def update_confidence(symbol, confidence):
    df = load_portfolio()
    df.loc[df["symbol"] == symbol, "confidence"] = confidence
    df.loc[df["symbol"] == symbol, "last_updated"] = datetime.now()
    save_portfolio(df)


def remove_position(symbol):
    df = load_portfolio()
    df = df[df["symbol"] != symbol]
    save_portfolio(df)