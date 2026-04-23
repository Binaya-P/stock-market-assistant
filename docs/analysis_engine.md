# Analysis Engine

## Overview

The analysis engine processes NEPSE floor-sheet data and generates ranked signals from:

- volume
- trade activity
- large-trade participation
- liquidity
- final score blending

The engine ranks opportunities first. The execution layer decides whether to buy, hold, upgrade, or exit.

## Core Metrics

### 1. Volume

Total traded quantity per stock.

### 2. Trades / Activity

Number of transactions per stock.

### 3. Average Price

Mean traded price.

### 4. Large Trade Ratio

Measures large-order participation:

`large traded quantity / total traded quantity`

## Normalization

To compare stocks in the same dataset:

- `volume_norm = volume / max(volume)`
- `activity_norm = trades / max(trades)`

## Confidence Score

`confidence = (large_trade_ratio * 0.4) + (volume_norm * 0.3) + (activity_norm * 0.3)`

Scaled to `0-100`.

## Liquidity Score

`liquidity_score = (volume_norm * 0.6) + (activity_norm * 0.4)`

Scaled to `0-100`.

## Final Score

`final_score = (confidence * 0.7) + (liquidity_score * 0.3)`

## Filtering Rules

To remove weak candidates:

- `volume >= 50,000`
- `trades >= 200`

The midday script uses lighter thresholds for earlier screening.

## Signal Classification

Current thresholds:

- `final_score >= 75` and `activity_norm >= 0.2` -> `BREAKOUT`
- `confidence >= 45` -> `ACCUMULATION`
- `confidence >= 35` -> `WATCH`
- otherwise -> `IGNORE`

## Interpretation

- `BREAKOUT` -> strongest momentum/liquidity candidate
- `ACCUMULATION` -> potential buy candidate
- `WATCH` -> monitor
- `IGNORE` -> discard

## Notes

- Scores are relative to the loaded dataset
- The model still uses static thresholds
- Liquidity is prioritized before portfolio actions

## Future Improvements

- market mode detection
- multi-timeframe signals
- momentum and trend integration
- volatility adjustment
- backtesting against historical snapshots
