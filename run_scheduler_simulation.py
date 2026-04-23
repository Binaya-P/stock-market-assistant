import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from collector.scheduler import simulate_scheduler_window


DEFAULT_OUTPUT = Path("data/summary/scheduler_simulation.csv")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate the NepseAI scheduler without running live jobs."
    )
    parser.add_argument("--start", required=True, help="Start datetime in ISO format, e.g. 2026-04-24T12:00")
    parser.add_argument("--end", required=True, help="End datetime in ISO format, e.g. 2026-06-30T20:00")
    parser.add_argument("--step-minutes", type=int, default=1, help="Simulation step in minutes")
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT), help="CSV output path")
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)

    events = simulate_scheduler_window(
        start=start,
        end=end,
        step_minutes=args.step_minutes,
    )

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(events)
    df.to_csv(output_path, index=False)

    print("\n=== SCHEDULER SIMULATION ===")
    print(f"events: {len(df)}")
    print(f"output: {output_path}")

    if df.empty:
        print("No scheduled jobs in the selected window.")
        return

    print("\n=== JOB COUNTS ===")
    print(df["job_name"].value_counts().to_string())
    print("\n=== FIRST EVENTS ===")
    print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
