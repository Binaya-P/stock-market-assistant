from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from nepse import Nepse


RAW_DATA_DIR = Path("data/raw")
SNAPSHOT_ID_FORMAT = "%Y%m%d_%H%M%S"


def _build_client() -> Nepse:
    client = Nepse()
    client.setTLSVerification(False)
    return client


def fetch_data(client: Optional[Nepse] = None) -> Optional[Path]:
    client = client or _build_client()
    collection_time = datetime.now().astimezone()
    snapshot_id = collection_time.strftime(SNAPSHOT_ID_FORMAT)

    try:
        data = client.getFloorSheet()
        df = pd.DataFrame(data)

        if df.empty:
            raise ValueError("NEPSE returned no floor sheet rows.")

        df["collectionTime"] = collection_time.isoformat(timespec="seconds")
        df["snapshotId"] = snapshot_id

        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        filename = RAW_DATA_DIR / f"floor_{snapshot_id}.csv"
        df.to_csv(filename, index=False)

        print(f"[OK] Saved {len(df)} rows to {filename}")
        return filename

    except Exception as exc:
        print(f"[ERROR] Fetch failed: {exc}")
        return None
