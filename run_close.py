from analysis.data_loader import load_all_data
from analysis.signals import generate_signals
from execution.decision_engine import process_signals


def main() -> None:
    df = load_all_data("data/")
    signals = generate_signals(df)

    print("\n=== TOP SIGNALS ===")
    if signals.empty:
        print("No stocks matched the current close-session thresholds.")
        return

    print(
        signals[
            ["stock", "confidence", "final_score", "system_signal", "avg_price"]
        ].head(10).to_string(index=False)
    )

    print("\n=== DECISIONS ===")
    decisions = process_signals(signals)

    if decisions.empty:
        print("No portfolio actions were generated.")
        return

    print(decisions.to_string(index=False))


if __name__ == "__main__":
    main()
