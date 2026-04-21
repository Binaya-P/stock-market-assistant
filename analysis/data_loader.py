import pandas as pd
import os

def load_all_data(folder_path):
    all_files = []

    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)
            df = df.drop_duplicates(subset="contractId")
            all_files.append(df)

    if not all_files:
        print("No CSV files found!")
        return pd.DataFrame()

    combined_df = pd.concat(all_files, ignore_index=True)

    return combined_df