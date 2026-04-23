from analysis.data_loader import build_snapshot_index


def main() -> None:
    snapshot_index = build_snapshot_index("data/")

    print("\n=== RAW DATA SNAPSHOT INDEX ===")
    if snapshot_index.empty:
        print("No raw floor-sheet snapshots found.")
        return

    print(
        snapshot_index[
            [
                "source_file",
                "snapshotId",
                "collectionTime",
                "businessDate",
                "rows",
                "symbols",
                "firstTradeTime",
                "lastTradeTime",
            ]
        ].head(20).to_string(index=False)
    )


if __name__ == "__main__":
    main()
