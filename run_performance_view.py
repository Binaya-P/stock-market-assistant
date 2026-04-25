import json

with open("data/state/virtual_performance.json") as f:
    perf = json.load(f)

print("\n=== PERFORMANCE ===")
print(f"Realized PnL: {perf['realized_pnl']}")
print(f"Trades: {perf['trade_count']}")
print(f"Wins: {perf['wins']}")
print(f"Losses: {perf['losses']}")

if perf["trade_count"] > 0:
    win_rate = perf["wins"] / perf["trade_count"] * 100
    print(f"Win Rate: {win_rate:.2f}%")