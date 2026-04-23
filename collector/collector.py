import pandas as pd
from datetime import datetime
from nepse import Nepse
import os

nepse = Nepse()
nepse.setTLSVerification(False)


def fetch_data():
    try:
        # Fetch data from NEPSE
        data = nepse.getFloorSheet()
        df = pd.DataFrame(data)

        # Ensure data folder exists
        os.makedirs("data", exist_ok=True)

        # Save file
        filename = f"data/raw/floor_{timestamp}.csv"
        df.to_csv(filename, index=False)

        print(f"[✔] Saved: {filename}")

        # 🔥 OPTIONAL: Auto Git sync (enable later for old laptop)
        # Comment these during testing if annoying
        os.system("git add data/")
        os.system(f'git commit -m "data {timestamp}"')
        os.system("git push")

    except Exception as e:
        print("[ERROR] Fetch failed:", e)


if __name__ == "__main__":
    fetch_data()