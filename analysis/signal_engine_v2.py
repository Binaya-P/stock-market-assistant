import pandas as pd

def calculate_signals(df):
    # -----------------------------
    # CLEAN INPUT
    # -----------------------------
    df.columns = df.columns.str.strip()

    results = []

    # Market baseline
    avg_trades_all = df.groupby("stockSymbol").size().mean()

    for stock, group in df.groupby("stockSymbol"):

        # -----------------------------
        # BASIC FILTERS
        # -----------------------------
        if len(group) < 20:
            continue

        group = group.sort_values("tradeTime")

        trade_count = len(group)
        total_volume = group["contractQuantity"].sum()

        start_price = group["contractRate"].iloc[0]
        end_price = group["contractRate"].iloc[-1]

        price_change = (end_price - start_price) / (start_price + 1e-6)

        # 🚫 Avoid already pumped stocks
        if price_change > 0.08:
            continue

        # -----------------------------
        # LARGE TRADE DETECTION
        # -----------------------------
        avg_qty = group["contractQuantity"].mean()
        large_trades = group[group["contractQuantity"] > avg_qty * 2]
        large_ratio = len(large_trades) / (trade_count + 1e-6)

        # -----------------------------
        # ACTIVITY SCORE
        # -----------------------------
        activity_score = trade_count / (avg_trades_all + 1e-6)

        # 🚫 Remove low participation stocks
        if activity_score < 0.2:
            continue

        activity_score = min(activity_score, 1)

        # -----------------------------
        # TREND STRENGTH
        # -----------------------------
        prices = group["contractRate"].values

        up_moves = sum(prices[i] > prices[i - 1] for i in range(1, len(prices)))
        down_moves = sum(prices[i] < prices[i - 1] for i in range(1, len(prices)))

        total_moves = up_moves + down_moves + 1e-6
        trend_strength = up_moves / total_moves

        results.append({
            "stock": stock,
            "volume": total_volume,
            "trades": trade_count,
            "price_change": price_change,
            "large_trade_ratio": large_ratio,
            "activity_score": activity_score,
            "trend_strength": trend_strength
        })

    # -----------------------------
    # CREATE DATAFRAME
    # -----------------------------
    df_res = pd.DataFrame(results)

    if df_res.empty:
        return df_res

    # -----------------------------
    # NORMALIZATION
    # -----------------------------
    for col in ["large_trade_ratio", "activity_score", "trend_strength"]:
        df_res[col] = (
            df_res[col] - df_res[col].min()
        ) / (
            df_res[col].max() - df_res[col].min() + 1e-6
        )

    # -----------------------------
    # PRICE STABILITY
    # -----------------------------
    price_stability = 1 - df_res["price_change"].clip(0, 0.08) / 0.08

    # -----------------------------
    # TREND PENALTY
    # -----------------------------
    trend_penalty = (df_res["trend_strength"] - 0.45).clip(lower=0) / 0.55

    # -----------------------------
    # FINAL CONFIDENCE SCORE (%)
    # -----------------------------
    df_res["confidence"] = (
        df_res["large_trade_ratio"] * 30 +
        df_res["activity_score"] * 25 +
        price_stability * 25 +
        trend_penalty * 20
    )

    df_res["confidence"] = df_res["confidence"].round(2)

    # -----------------------------
    # HYBRID CLASSIFICATION
    # -----------------------------
    df_res["rank"] = df_res["confidence"].rank(method="first", ascending=False)

    total_stocks = len(df_res)

    top_n = max(3, int(total_stocks * 0.1))
    watch_n = max(6, int(total_stocks * 0.3))

    def classify(row):
        if row["confidence"] > 75 and row["rank"] <= top_n:
            return "BUY"
        elif row["confidence"] > 65 and row["rank"] <= watch_n:
            return "WATCH"
        else:
            return "AVOID"

    df_res["signal"] = df_res.apply(classify, axis=1)

    # -----------------------------
    # FINAL OUTPUT
    # -----------------------------
    return df_res.sort_values(by="confidence", ascending=False)