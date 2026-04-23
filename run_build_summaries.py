from analysis.dataset_builder import build_pipeline_artifacts, write_pipeline_exports
from storage.sqlite_store import sync_pipeline_to_sqlite


def main() -> None:
    artifacts = build_pipeline_artifacts("data/")
    written_files = write_pipeline_exports(artifacts)
    sqlite_path = sync_pipeline_to_sqlite(artifacts)

    print("\n=== SUMMARY FILES UPDATED ===")
    for period_type, file_path in written_files.items():
        print(f"{period_type}: {file_path}")
    print(f"sqlite: {sqlite_path}")


if __name__ == "__main__":
    main()
