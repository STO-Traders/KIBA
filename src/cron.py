"""Cron scheduling for Kiba — persistent scheduled `kiba` runs.

Jobs persist in ~/.kiba/crons.json. A standard 5-field cron expression
(minute hour day-of-month month day-of-week) decides when each job's prompt runs
headlessly (via the SDK). Drive it with `kiba cron run` from your watchdog, a
LaunchAgent, or Windows Task Scheduler.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path

CRON_PATH = Path.home() / ".kiba" / "crons.json"


def _load() -> list[dict]:
    try:
        if CRON_PATH.is_file():
            data = json.loads(CRON_PATH.read_text(encoding="utf-8"))
            return data.get("jobs", []) if isinstance(data, dict) else []
    except Exception:
        pass
    return []


def _save(jobs: list[dict]) -> None:
    CRON_PATH.parent.mkdir(parents=True, exist_ok=True)
    CRON_PATH.write_text(json.dumps({"jobs": jobs}, indent=2), encoding="utf-8")


def add_job(schedule: str, prompt: str) -> dict:
    jobs = _load()
    job = {"id": uuid.uuid4().hex[:8], "schedule": schedule, "prompt": prompt,
           "enabled": True, "last_run": None}
    jobs.append(job)
    _save(jobs)
    return job


def list_jobs() -> list[dict]:
    return _load()


def remove_job(job_id: str) -> bool:
    jobs = _load()
    kept = [j for j in jobs if j.get("id") != job_id]
    if len(kept) == len(jobs):
        return False
    _save(kept)
    return True


def _match(expr: str, value: int, lo: int) -> bool:
    expr = expr.strip()
    if expr == "*":
        return True
    for part in expr.split(","):
        part = part.strip()
        try:
            step = 1
            if "/" in part:
                rng, s = part.split("/", 1)
                step = int(s)
                part = rng.strip()
            if step <= 0:
                continue
            if part == "*":
                if (value - lo) % step == 0:
                    return True
            elif "-" in part:
                a, b = part.split("-")
                a, b = int(a), int(b)
                if a <= value <= b and (value - a) % step == 0:
                    return True
            else:
                if int(part) == value:
                    return True
        except Exception:
            continue
    return False


def is_due(schedule: str, now: datetime) -> bool:
    """True if a 5-field cron expression matches `now` (minute resolution)."""
    f = schedule.split()
    if len(f) != 5:
        return False
    dow = (now.weekday() + 1) % 7  # cron: Sun=0..Sat=6 ; python Mon=0..Sun=6
    dow_ok = _match(f[4], dow, 0) or (dow == 0 and _match(f[4], 7, 0))  # Sunday is 0 OR 7
    return (
        _match(f[0], now.minute, 0)
        and _match(f[1], now.hour, 0)
        and _match(f[2], now.day, 1)
        and _match(f[3], now.month, 1)
        and dow_ok
    )


def run_due(now: datetime | None = None, runner=None) -> list[str]:
    """Fire every enabled job due at `now`. De-dupes within the same minute. Returns ids fired."""
    now = now or datetime.now()
    stamp = now.strftime("%Y-%m-%dT%H:%M")
    jobs = _load()
    fired: list[str] = []
    for job in jobs:
        if not job.get("enabled", True) or job.get("last_run") == stamp:
            continue
        if is_due(job.get("schedule", ""), now):
            r = runner
            try:
                if r is None:
                    from src.sdk import query
                    r = query
                r(job["prompt"])
            except Exception as e:
                import sys as _sys
                print(f"kiba cron: job {job.get('id')} failed: {e}", file=_sys.stderr)
                continue  # don't mark run -> retried next minute, error surfaced
            job["last_run"] = stamp
            fired.append(job["id"])
    if fired:
        _save(jobs)
    return fired


def run_scheduler(tick: int = 60) -> None:
    """Loop forever, firing due jobs each minute. Run from a watchdog/LaunchAgent."""
    while True:
        run_due()
        now = datetime.now()
        time.sleep(max(1, tick - now.second))
