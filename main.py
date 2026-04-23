from analysis.data_loader import load_all_data
from analysis.signals import generate_signals

df = load_all_data("data/raw/")
signals = generate_signals(df)

print(signals.head(5))