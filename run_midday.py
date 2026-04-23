from analysis.data_loader import load_all_data
from analysis.signals import generate_signals


def main() -> None:
    df = load_all_data("data/")
    signals = generate_signals(df, min_volume=10000, min_trades=50)

    print("\n=== MIDDAY SIGNALS ===")
    if signals.empty:
        print("No midday candidates matched the current thresholds.")
        return

    print(
        signals[
            ["stock", "confidence", "final_score", "system_signal", "volume", "trades"]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()
