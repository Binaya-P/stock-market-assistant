from analysis.data_loader import load_all_data
from analysis.signals import generate_signals
from execution.decision_engine import process_signals


def main():
    df = load_all_data("data/")
    signals = generate_signals(df)

    print("\n=== TOP SIGNALS ===")
    print(signals.head(10))

    print("\n=== DECISIONS ===")
    process_signals(signals)


if __name__ == "__main__":
    main()