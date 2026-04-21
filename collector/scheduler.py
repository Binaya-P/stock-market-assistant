import time
from datetime import datetime
from collector.collector import fetch_data


def is_market_time():
    now = datetime.now()

    # Monday=0, Sunday=6
    if now.weekday() > 4:
        return False

    hour = now.hour

    # 10 AM → 4 PM (includes buffer)
    return 10 <= hour <= 16


def run_scheduler(interval=1800):  # 30 minutes
    print("[INFO] Scheduler started...")

    while True:
        if is_market_time():
            print("[INFO] Collecting data...")
            fetch_data()
            time.sleep(interval)
        else:
            print("[INFO] Market closed. Sleeping...")
            time.sleep(600)