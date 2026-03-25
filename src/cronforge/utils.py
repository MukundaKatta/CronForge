"""Utility functions for CronForge — cron field parsing, NL pattern matching, date calculation."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import List, Optional, Set, Tuple

from cronforge.config import CRON_FIELDS, DAY_NAMES, MONTH_NAMES, WEEKDAY_LABELS


# ---------------------------------------------------------------------------
# Cron field parsing
# ---------------------------------------------------------------------------

def parse_cron_field(field_value: str, field_name: str) -> Set[int]:
    """Parse a single cron field into a set of matching integer values.

    Supports: *, */N, N, N-M, N-M/S, and comma-separated combinations.
    """
    bounds = CRON_FIELDS[field_name]
    lo, hi = bounds["min"], bounds["max"]
    result: Set[int] = set()

    for part in field_value.split(","):
        part = part.strip()

        # Wildcard
        if part == "*":
            result.update(range(lo, hi + 1))

        # Step on wildcard: */N
        elif part.startswith("*/"):
            step = int(part[2:])
            if step <= 0:
                raise ValueError(f"Invalid step value in '{field_value}'")
            result.update(range(lo, hi + 1, step))

        # Range with optional step: N-M or N-M/S
        elif "-" in part:
            range_part, *step_part = part.split("/")
            start_str, end_str = range_part.split("-", 1)
            start, end = int(start_str), int(end_str)
            step = int(step_part[0]) if step_part else 1
            if start < lo or end > hi or start > end or step <= 0:
                raise ValueError(f"Invalid range in '{field_value}' for {field_name}")
            result.update(range(start, end + 1, step))

        # Single value
        else:
            val = int(part)
            if val < lo or val > hi:
                raise ValueError(
                    f"Value {val} out of range [{lo}-{hi}] for {field_name}"
                )
            result.add(val)

    return result


def validate_cron_field(field_value: str, field_name: str) -> bool:
    """Return True if a single cron field string is syntactically valid."""
    try:
        parse_cron_field(field_value, field_name)
        return True
    except (ValueError, IndexError):
        return False


# ---------------------------------------------------------------------------
# Natural-language pattern matching
# ---------------------------------------------------------------------------

_NL_PATTERNS: List[Tuple[re.Pattern, callable]] = []


def _register(pattern: str):
    """Decorator to register an NL pattern handler."""
    compiled = re.compile(pattern, re.IGNORECASE)

    def decorator(fn):
        _NL_PATTERNS.append((compiled, fn))
        return fn

    return decorator


def _parse_time(time_str: str) -> Tuple[int, int]:
    """Parse a time string like '3pm', '9am', '14:30', 'midnight', 'noon' into (hour, minute)."""
    time_str = time_str.strip().lower()

    if time_str in ("midnight",):
        return 0, 0
    if time_str in ("noon",):
        return 12, 0

    # 8:30am, 2:15pm
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)?$", time_str)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        period = m.group(3)
        if period == "pm" and hour < 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        return hour, minute

    # 3pm, 9am
    m = re.match(r"^(\d{1,2})\s*(am|pm)$", time_str)
    if m:
        hour = int(m.group(1))
        period = m.group(2)
        if period == "pm" and hour < 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        return hour, 0

    # 24-hour bare number
    m = re.match(r"^(\d{1,2})$", time_str)
    if m:
        return int(m.group(1)), 0

    raise ValueError(f"Cannot parse time: '{time_str}'")


def _day_to_num(day_str: str) -> int:
    """Convert a day name to cron weekday number (0=Sun)."""
    key = day_str.strip().lower()
    if key in DAY_NAMES:
        return DAY_NAMES[key]
    raise ValueError(f"Unknown day name: '{day_str}'")


# --- Registered NL patterns ---

@_register(r"^every\s+minute$")
def _every_minute(m):
    return "* * * * *"


@_register(r"^every\s+(\d+)\s+minutes?$")
def _every_n_minutes(m):
    n = int(m.group(1))
    return f"*/{n} * * * *"


@_register(r"^every\s+hour$")
def _every_hour(m):
    return "0 * * * *"


@_register(r"^every\s+(\d+)\s+hours?$")
def _every_n_hours(m):
    n = int(m.group(1))
    return f"0 */{n} * * *"


@_register(r"^hourly\s+at\s+:(\d{2})$")
def _hourly_at(m):
    minute = int(m.group(1))
    return f"{minute} * * * *"


@_register(r"^daily\s+at\s+(.+)$")
def _daily_at(m):
    hour, minute = _parse_time(m.group(1))
    return f"{minute} {hour} * * *"


@_register(r"^every\s+(\w+)\s+at\s+(.+)$")
def _every_day_at(m):
    day_str = m.group(1)
    time_str = m.group(2)
    day_num = _day_to_num(day_str)
    hour, minute = _parse_time(time_str)
    return f"{minute} {hour} * * {day_num}"


@_register(r"^weekdays\s+at\s+(.+)$")
def _weekdays_at(m):
    hour, minute = _parse_time(m.group(1))
    return f"{minute} {hour} * * 1-5"


@_register(r"^weekends?\s+at\s+(.+)$")
def _weekends_at(m):
    hour, minute = _parse_time(m.group(1))
    return f"{minute} {hour} * * 0,6"


@_register(r"^first\s+of\s+every\s+month$")
def _first_of_month(m):
    return "0 0 1 * *"


@_register(r"^first\s+of\s+every\s+month\s+at\s+(.+)$")
def _first_of_month_at(m):
    hour, minute = _parse_time(m.group(1))
    return f"{minute} {hour} 1 * *"


@_register(r"^every\s+day$")
def _every_day(m):
    return "0 0 * * *"


@_register(r"^annually$|^yearly$")
def _yearly(m):
    return "0 0 1 1 *"


def match_natural_language(description: str) -> Optional[str]:
    """Try to match a natural-language description to a cron expression.

    Returns the cron expression string on success, or None if no pattern matches.
    """
    description = description.strip()
    for pattern, handler in _NL_PATTERNS:
        m = pattern.match(description)
        if m:
            return handler(m)
    return None


# ---------------------------------------------------------------------------
# Date calculation helpers
# ---------------------------------------------------------------------------

def expand_cron(cron_expr: str) -> Tuple[Set[int], Set[int], Set[int], Set[int], Set[int]]:
    """Expand a full cron expression into sets of valid values for each field."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5 fields, got {len(parts)}: '{cron_expr}'")

    field_names = ["minute", "hour", "day", "month", "weekday"]
    return tuple(parse_cron_field(p, f) for p, f in zip(parts, field_names))


def matches_cron(dt: datetime, minutes: Set[int], hours: Set[int],
                 days: Set[int], months: Set[int], weekdays: Set[int]) -> bool:
    """Check whether a datetime matches expanded cron field sets."""
    cron_weekday = dt.isoweekday() % 7  # Convert: Mon=1..Sun=7 -> Sun=0..Sat=6
    return (
        dt.minute in minutes
        and dt.hour in hours
        and dt.day in days
        and dt.month in months
        and cron_weekday in weekdays
    )


def next_matching_times(
    cron_expr: str,
    count: int = 5,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    max_iterations: int = 525_960,  # ~1 year of minutes
) -> List[datetime]:
    """Compute the next *count* datetimes matching *cron_expr*, starting from *start*.

    If *end* is provided, stops early when the candidate exceeds *end*.
    """
    if start is None:
        start = datetime.utcnow().replace(second=0, microsecond=0) + timedelta(minutes=1)
    else:
        start = start.replace(second=0, microsecond=0)

    minutes, hours, days, months, weekdays = expand_cron(cron_expr)
    results: List[datetime] = []
    current = start
    iterations = 0

    while len(results) < count and iterations < max_iterations:
        if end and current > end:
            break
        if matches_cron(current, minutes, hours, days, months, weekdays):
            results.append(current)
        current += timedelta(minutes=1)
        iterations += 1

    return results


# ---------------------------------------------------------------------------
# Explanation helpers
# ---------------------------------------------------------------------------

def explain_field(field_value: str, field_name: str) -> str:
    """Produce a short human-readable explanation of one cron field."""
    if field_value == "*":
        return "every " + field_name

    if field_value.startswith("*/"):
        step = field_value[2:]
        return f"every {step} {field_name}s"

    if "-" in field_value and field_name == "weekday":
        lo, hi = field_value.split("-", 1)
        lo_label = WEEKDAY_LABELS.get(int(lo), lo)
        hi_label = WEEKDAY_LABELS.get(int(hi), hi)
        return f"{lo_label} through {hi_label}"

    if field_name == "weekday":
        parts = field_value.split(",")
        labels = [WEEKDAY_LABELS.get(int(p.strip()), p) for p in parts]
        return ", ".join(labels)

    return field_value
