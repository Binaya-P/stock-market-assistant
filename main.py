from data_loader import load_data
from signals import smart_signal

df = load_data("data/floor.csv")

result = smart_signal(df)

print(result.head(10))