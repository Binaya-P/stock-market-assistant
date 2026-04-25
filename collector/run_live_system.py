import time

from collector.collector import fetch_data
from execution.virtual_trader import run_virtual_trader
from execution.performance_tracker import update_performance
import json


def load_interval():
    with open("config/system_config.json") as f:
        return json.load(f)["scheduler"]["interval_minutes"] * 60


def run():

    print("Starting live system...")

    while True:
        try:
            print("\n--- CYCLE START ---")

            fetch_data()
            run_virtual_trader()
            update_performance()

            print("--- CYCLE END ---")

        except Exception as e:
            print("Error:", e)

        time.sleep(load_interval())


if __name__ == "__main__":
    run()