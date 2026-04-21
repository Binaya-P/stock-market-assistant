from analysis.data_loader import load_all_data
from analysis.signal_engine_v2 import calculate_signals

df = load_all_data("data/")
signals = calculate_signals(df)

print(signals.head(10))