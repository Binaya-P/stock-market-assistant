import pandas as pd


def large_trade_ratio(df, threshold=1000):
    def calc(group):
        total = group["contractQuantity"].sum()
        large = group[group["contractQuantity"] > threshold]["contractQuantity"].sum()
        return large / total if total != 0 else 0

    return df.groupby("stockSymbol").apply(calc)


def avg_price(df):
    return df.groupby("stockSymbol")["contractRate"].mean()


def repeat_activity(df):
    return df.groupby("stockSymbol")["contractId"].count()


def generate_signals(df):
    volume = df.groupby("stockSymbol")["contractQuantity"].sum()
    trades = df.groupby("stockSymbol")["contractId"].count()
    price = avg_price(df)
    large_ratio = large_trade_ratio(df)
    activity = repeat_activity(df)

    result = pd.DataFrame({
        "stock": volume.index,
        "volume": volume.values,
        "trades": trades.values,
        "avg_price": price.values,
        "large_trade_ratio": large_ratio.values,
        "activity": activity.values
    })

    # Normalize
    result["volume_norm"] = result["volume"] / result["volume"].max()
    result["activity_norm"] = result["activity"] / result["activity"].max()

    # Confidence (YOUR 60/40 idea)
    result["confidence"] = (
        (result["large_trade_ratio"] * 0.4) +
        (result["volume_norm"] * 0.3) +
        (result["activity_norm"] * 0.3)
    ) * 100


    result = result[
        (result["volume"] > 50000) & 
        (result["trades"] > 200)
    ]

    result["liquidity_score"] = (
        result["volume_norm"] * 0.6 +
        result["activity_norm"] * 0.4
    )


    # Final score (hybrid)
    result["final_score"] =result["final_score"] = (
        result["confidence"] * 0.7 +
        result["liquidity_score"] * 0.3
    )

    # Signal classification
    def classify_signal(row):
        if row["confidence"] > 75 and row["activity_norm"] > 0.2:
            return "BREAKOUT"
        elif row["confidence"] > 45:
            return "ACCUMULATION"
        elif row["confidence"] > 35:
            return "WATCH"
        else:
            return "IGNORE"

    result["system_signal"] = result.apply(classify_signal, axis=1)

    # Filter noise
    result = result[result["volume"] > 5000]

    return result.sort_values(by="confidence", ascending=False)