# Analysis Engine (Signal Engine v2)

## Overview
The Analysis Engine processes cleaned NEPSE floor sheet data and generates trading signals based on:

- Volume
- Trade activity
- Large trade participation
- Liquidity

It does NOT execute trades. It only provides ranked opportunities.

---

## Core Metrics

### 1. Volume
Total traded quantity per stock.

### 2. Trades (Activity)
Number of transactions per stock.

### 3. Average Price
Mean traded price.

### 4. Large Trade Ratio
Measures smart money presence:
large trades / total volume

---

## Normalization

To compare across stocks:

- volume_norm = volume / max(volume)
- activity_norm = trades / max(trades)

---

## Confidence Score

Balanced scoring:

confidence =  
(large_trade_ratio * 0.4) +  
(volume_norm * 0.3) +  
(activity_norm * 0.3)

Scaled to 0–100.

---

## Liquidity Score

liquidity_score =  
(volume_norm * 0.6) +  
(activity_norm * 0.4)

---

## Final Score

final_score =  
(confidence * 0.7) +  
(liquidity_score * 0.3)

---

## Filtering Rules

To remove noise:

- volume > 50,000
- trades > 200

---

## Signal Classification

Static thresholds (current version):

- confidence >= 45 → ACCUMULATION
- confidence >= 35 → WATCH
- else → IGNORE

---

## Interpretation

- ACCUMULATION → strong candidate (possible BUY)
- WATCH → monitor / wishlist
- IGNORE → discard

---

## Notes

- System is **market-relative but not fully adaptive yet**
- Designed for **liquidity-first filtering**
- Avoids illiquid trap stocks

---

## Future Improvements

- Market mode detection (bull/bear)
- Multi-timeframe signals
- Momentum + trend integration
- Volatility adjustment