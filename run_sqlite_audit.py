import sqlite3
from pathlib import Path


DB_PATH = Path("data/state/nepseai.db")


def main() -> None:
    print("\n=== SQLITE AUDIT ===")
    print(f"path: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    with sqlite3.connect(DB_PATH) as conn:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]

        if not tables:
            print("No tables found.")
            return

        for table_name in tables:
            row_count = conn.execute(
                f"SELECT COUNT(*) FROM [{table_name}]"
            ).fetchone()[0]
            print(f"{table_name}: {row_count}")


if __name__ == "__main__":
    main()
