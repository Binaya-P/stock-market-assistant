from nepse import Nepse
from collector.market_utils import is_collection_window

# import your existing collector function
from collector.floor_sheet_collector import collect_floor_sheet


def run():
    nepse = Nepse()

    if not is_collection_window(nepse):
        print("[INFO] Skipping collection (outside trading window)")
        return

    print("[INFO] Running floor sheet collection...")
    collect_floor_sheet(nepse)


if __name__ == "__main__":
    run() 