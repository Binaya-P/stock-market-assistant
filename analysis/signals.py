import pandas as pd

def large_trade_ratio(df, threshold=1000):
    def calc(group):
        total = group["contractQuantity"].sum()
        large = group[group["contractQuantity"] > threshold]["contractQuantity"].sum()
        return large / total if total != 0 else 0

    return df.groupby("stockSymbol").apply(calc)


def avg_price(df):
    return df.groupby("stockSymbol")["contractRate"].mean()


def smart_signal(df):
    volume = df.groupby("stockSymbol")["contractQuantity"].sum()
    large_ratio = large_trade_ratio(df)
    price = avg_price(df)

    result = volume.to_frame("volume")
    result["large_ratio"] = large_ratio
    result["avg_price"] = price

    # confidence score
    result["confidence"] = (
        (result["large_ratio"] * 0.6) +
        (result["volume"] / result["volume"].max() * 0.4)
    )

    # filter noise
    result = result[result["volume"] > 5000]

    return result.sort_values(by="confidence", ascending=False)

result["activity"] = repeat_activity(df)

result["final_score"] = (
    result["confidence"] * 0.7 +
    (result["activity"] / result["activity"].max()) * 0.3
)