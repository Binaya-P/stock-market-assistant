import pandas as pd
import glob

def load_all_data():
    files = glob.glob("data/floor_*.csv")
    df_list = [pd.read_csv(f) for f in files]
    return pd.concat(df_list, ignore_index=True)

df["timestamp"] = timestamp


def repeat_activity(df):
    return df.groupby("stockSymbol")["timestamp"].nunique()