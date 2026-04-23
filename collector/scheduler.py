import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from analysis.data_loader import load_data_bundle
from analysis.dataset_builder import (
    build_pipeline_artifacts,
    write_selected_summary_exports,
)
from storage.sqlite_store import (
    get_job_run_count,
    job_run_exists,
    record_job_run,
    sync_raw_bundle_to_sqlite,
    sync_selected_summaries_to_sqlite,
)


RAW_FETCH_JOBS = {
    "raw_fetch_1300": {"hour": 13, "minute": 0},
    "raw_fetch_1530": {"hour": 15, "minute": 30},
}

SUMMARY_JOB_CONFIG = {
    "daily_summary": {"hour": 16, "minute": 0, "period_types": ["daily"]},
    "weekly_summary": {"hour": 17, "minute": 0, "period_types": ["weekly"]},
    "fortnightly_summary": {"hour": 18, "minute": 0, "period_types": ["fortnightly"]},
    "monthly_summary": {"hour": 19, "minute": 0, "period_types": ["monthly"]},
    "yearly_summary": {"hour": 20, "minute": 0, "period_types": ["yearly"]},
}


@dataclass
class SchedulerSimulationState:
    job_counts: Dict[str, int] = field(default_factory=dict)
    last_run_slots: Dict[str, str] = field(default_factory=dict)
    persisted_slots: Dict[str, set] = field(default_factory=dict)


def is_trading_day(now: Optional[datetime] = None) -> bool:
    current = now or datetime.now()
    return current.weekday() < 5


def _matches_minute_slot(now: datetime, hour: int, minute: int) -> bool:
    return now.hour == hour and now.minute == minute


def _run_key(now: datetime) -> str:
    return now.strftime("%Y%m%d_%H%M")


def _archive_tag(now: datetime) -> str:
    return now.strftime("%Y%m%d_%H%M%S")


def _job_already_ran(
    job_name: str,
    slot_key: str,
    last_run_slots: Dict[str, str],
) -> bool:
    return last_run_slots.get(job_name) == slot_key


def _should_run_cycle(job_name: str, job_counts: Dict[str, int]) -> bool:
    if job_name == "fortnightly_summary":
        weekly_runs = job_counts.get("weekly_summary", 0)
        return weekly_runs > 0 and weekly_runs % 2 == 0
    if job_name == "monthly_summary":
        fortnightly_runs = job_counts.get("fortnightly_summary", 0)
        return fortnightly_runs > 0 and fortnightly_runs % 2 == 0
    if job_name == "yearly_summary":
        monthly_runs = job_counts.get("monthly_summary", 0)
        return monthly_runs > 0 and monthly_runs % 12 == 0
    return True


def plan_scheduler_jobs(
    now: datetime,
    job_counts: Optional[Dict[str, int]] = None,
    last_run_slots: Optional[Dict[str, str]] = None,
    persisted_slots: Optional[Dict[str, set]] = None,
) -> List[str]:
    effective_counts = dict(job_counts or {})
    effective_last_slots = dict(last_run_slots or {})
    effective_persisted_slots = {
        key: set(value) for key, value in (persisted_slots or {}).items()
    }

    slot_key = _run_key(now)
    planned_jobs: List[str] = []

    def can_run(job_name: str) -> bool:
        if _job_already_ran(job_name, slot_key, effective_last_slots):
            return False
        if slot_key in effective_persisted_slots.get(job_name, set()):
            return False
        return True

    if is_trading_day(now):
        for job_name, config in RAW_FETCH_JOBS.items():
            if _matches_minute_slot(now, config["hour"], config["minute"]) and can_run(job_name):
                planned_jobs.append(job_name)
                effective_last_slots[job_name] = slot_key
                effective_persisted_slots.setdefault(job_name, set()).add(slot_key)
                effective_counts[job_name] = effective_counts.get(job_name, 0) + 1

        daily_config = SUMMARY_JOB_CONFIG["daily_summary"]
        if _matches_minute_slot(now, daily_config["hour"], daily_config["minute"]) and can_run("daily_summary"):
            planned_jobs.append("daily_summary")
            effective_last_slots["daily_summary"] = slot_key
            effective_persisted_slots.setdefault("daily_summary", set()).add(slot_key)
            effective_counts["daily_summary"] = effective_counts.get("daily_summary", 0) + 1

    if now.weekday() == 4:
        for job_name in ["weekly_summary", "fortnightly_summary", "monthly_summary", "yearly_summary"]:
            config = SUMMARY_JOB_CONFIG[job_name]
            if not _matches_minute_slot(now, config["hour"], config["minute"]):
                continue
            if not can_run(job_name):
                continue
            if not _should_run_cycle(job_name, effective_counts):
                continue
            planned_jobs.append(job_name)
            effective_last_slots[job_name] = slot_key
            effective_persisted_slots.setdefault(job_name, set()).add(slot_key)
            effective_counts[job_name] = effective_counts.get(job_name, 0) + 1

    return planned_jobs


def _fetch_and_sync_raw(raw_folder_path: str) -> None:
    from collector.collector import fetch_data

    result = fetch_data()
    if result is None:
        return

    data_bundle = load_data_bundle(raw_folder_path)
    sqlite_path = sync_raw_bundle_to_sqlite(data_bundle)
    print(f"[INFO] Raw SQLite synchronized: {sqlite_path}")


def _build_and_sync_selected_summaries(
    raw_folder_path: str,
    period_types: list[str],
    job_name: str,
    now: datetime,
    slot_key: str,
) -> None:
    artifacts = build_pipeline_artifacts(raw_folder_path)
    run_tag = _archive_tag(now)
    written_files = write_selected_summary_exports(artifacts, period_types, run_tag)
    sqlite_path = sync_selected_summaries_to_sqlite(artifacts, period_types)
    record_job_run(job_name, period_key=slot_key, notes=run_tag)

    print(
        "[INFO] Summary files updated:",
        ", ".join(f"{name}={path}" for name, path in written_files.items()),
    )
    print(f"[INFO] SQLite synchronized: {sqlite_path}")


def _load_live_job_counts() -> Dict[str, int]:
    job_names = list(RAW_FETCH_JOBS.keys()) + list(SUMMARY_JOB_CONFIG.keys())
    return {job_name: get_job_run_count(job_name) for job_name in job_names}


def _persisted_slot_map(job_names: List[str], slot_key: str) -> Dict[str, set]:
    persisted = {}
    for job_name in job_names:
        if job_run_exists(job_name, slot_key):
            persisted[job_name] = {slot_key}
    return persisted


def _execute_job(job_name: str, now: datetime, slot_key: str, raw_folder_path: str) -> None:
    if job_name in RAW_FETCH_JOBS:
        print(f"[INFO] Running scheduled raw fetch for {job_name}...")
        _fetch_and_sync_raw(raw_folder_path)
        record_job_run(job_name, period_key=slot_key)
        return

    period_types = SUMMARY_JOB_CONFIG[job_name]["period_types"]
    print(f"[INFO] Updating {job_name}...")
    _build_and_sync_selected_summaries(
        raw_folder_path,
        period_types,
        job_name,
        now,
        slot_key,
    )


def run_scheduler(
    idle_interval: int = 20,
    raw_folder_path: str = "data/raw/",
) -> None:
    print("[INFO] Scheduler started...")

    last_run_slots: Dict[str, str] = {}
    job_names = list(RAW_FETCH_JOBS.keys()) + list(SUMMARY_JOB_CONFIG.keys())

    while True:
        now = datetime.now()
        slot_key = _run_key(now)

        try:
            job_counts = _load_live_job_counts()
            persisted_slots = _persisted_slot_map(job_names, slot_key)
            planned_jobs = plan_scheduler_jobs(
                now,
                job_counts=job_counts,
                last_run_slots=last_run_slots,
                persisted_slots=persisted_slots,
            )

            for job_name in planned_jobs:
                _execute_job(job_name, now, slot_key, raw_folder_path)
                last_run_slots[job_name] = slot_key

        except Exception as exc:
            print(f"[ERROR] Scheduler task failed: {exc}")

        time.sleep(idle_interval)


def simulate_scheduler_window(
    start: datetime,
    end: datetime,
    step_minutes: int = 1,
    initial_job_counts: Optional[Dict[str, int]] = None,
) -> List[Dict[str, object]]:
    if end < start:
        raise ValueError("end must be greater than or equal to start")

    state = SchedulerSimulationState(job_counts=dict(initial_job_counts or {}))
    events: List[Dict[str, object]] = []
    current = start

    while current <= end:
        planned_jobs = plan_scheduler_jobs(
            current,
            job_counts=state.job_counts,
            last_run_slots=state.last_run_slots,
            persisted_slots=state.persisted_slots,
        )

        for job_name in planned_jobs:
            slot_key = _run_key(current)
            state.job_counts[job_name] = state.job_counts.get(job_name, 0) + 1
            state.last_run_slots[job_name] = slot_key
            state.persisted_slots.setdefault(job_name, set()).add(slot_key)
            events.append(
                {
                    "scheduled_time": current.isoformat(timespec="minutes"),
                    "job_name": job_name,
                    "slot_key": slot_key,
                    "resulting_run_count": state.job_counts[job_name],
                }
            )

        current += timedelta(minutes=step_minutes)

    return events
