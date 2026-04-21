def top_volume(df):
    return df.groupby("stockSymbol")["contractQuantity"].sum()


def large_trade_ratio(df, threshold=1000):
    def calc(group):
        total = group["contractQuantity"].sum()
        large = group[group["contractQuantity"] > threshold]["contractQuantity"].sum()
        return large / total if total != 0 else 0

    return df.groupby("stockSymbol").apply(calc)


def avg_price(df):
    return df.groupby("stockSymbol")["contractRate"].mean()