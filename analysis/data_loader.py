import pandas as pd
import os


def load_all_data(folder_path="data/raw/"):
    all_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith(".csv")
    ]

    df_list = [pd.read_csv(file) for file in all_files]

    combined = pd.concat(df_list, ignore_index=True)

    return combined