"""Google Calendar listing, free-slot search, and event creation helpers."""

from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from l06.google_client import TIMEZONE, build_calendar_service

JERUSALEM_TZ = ZoneInfo(TIMEZONE)
WORKDAY_START = time(8, 0)
WORKDAY_END = time(20, 0)


def _to_jerusalem_dt(value: str) -> datetime:
    """Parse an ISO-8601 datetime string and normalize it to Asia/Jerusalem."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=JERUSALEM_TZ)
    return dt.astimezone(JERUSALEM_TZ)


def list_events(days_ahead: int = 7) -> list[dict[str, Any]]:
    """List primary calendar events from now through days_ahead days."""
    days = max(1, min(days_ahead, 90))
    now = datetime.now(JERUSALEM_TZ)
    end = now + timedelta(days=days)

    service = build_calendar_service()
    resp = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            timeZone=TIMEZONE,
        )
        .execute()
    )
    events: list[dict[str, Any]] = []
    for ev in resp.get("items", []):
        start_obj = ev.get("start", {})
        end_obj = ev.get("end", {})
        events.append(
            {
                "id": ev.get("id", ""),
                "summary": ev.get("summary", "(No title)"),
                "start": start_obj.get("dateTime") or start_obj.get("date", ""),
                "end": end_obj.get("dateTime") or end_obj.get("date", ""),
                "location": ev.get("location", ""),
                "description": ev.get("description", ""),
                "status": ev.get("status", ""),
            }
        )
    return events


def _merge_intervals(
    intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Merge overlapping or adjacent [start, end] datetime intervals."""
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda item: item[0])
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def find_free_slots(date: str, duration_minutes: int = 30) -> list[dict[str, Any]]:
    """Find free slots on YYYY-MM-DD (08:00-20:00 Asia/Jerusalem)."""
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be positive")

    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    window_start = datetime.combine(target_date, WORKDAY_START, tzinfo=JERUSALEM_TZ)
    window_end = datetime.combine(target_date, WORKDAY_END, tzinfo=JERUSALEM_TZ)

    service = build_calendar_service()
    fb = service.freebusy().query(
        body={
            "timeMin": window_start.isoformat(),
            "timeMax": window_end.isoformat(),
            "timeZone": TIMEZONE,
            "items": [{"id": "primary"}],
        }
    ).execute()
    raw_busy = fb.get("calendars", {}).get("primary", {}).get("busy", [])
    clipped = [
        (max(window_start, _to_jerusalem_dt(b["start"])), min(window_end, _to_jerusalem_dt(b["end"])))
        for b in raw_busy
    ]
    busy = _merge_intervals([(s, e) for s, e in clipped if s < e])

    min_delta = timedelta(minutes=duration_minutes)
    free: list[dict[str, Any]] = []
    cursor = window_start
    for b_start, b_end in [*busy, (window_end, window_end)]:
        if b_start - cursor >= min_delta:
            free.append({
                "start": cursor.isoformat(),
                "end": b_start.isoformat(),
                "duration_minutes": int((b_start - cursor).total_seconds() // 60),
            })
        cursor = max(cursor, b_end)
    return free


def create_event(
    title: str, start: str, end: str, description: str = ""
) -> dict[str, Any]:
    """Create a Google Calendar event in Asia/Jerusalem timezone."""
    start_dt = _to_jerusalem_dt(start)
    end_dt = _to_jerusalem_dt(end)
    if end_dt <= start_dt:
        raise ValueError("end must be after start")

    body: dict[str, Any] = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
    }
    service = build_calendar_service()
    created = service.events().insert(calendarId="primary", body=body).execute()
    return {
        "id": created.get("id", ""),
        "title": created.get("summary", title),
        "start": created.get("start", {}).get("dateTime", start_dt.isoformat()),
        "end": created.get("end", {}).get("dateTime", end_dt.isoformat()),
        "html_link": created.get("htmlLink", ""),
        "status": created.get("status", "confirmed"),
    }
