import pandas as pd

def load_data(path="data/floor.csv"):
    return pd.read_csv(path)