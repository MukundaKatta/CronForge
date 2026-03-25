"""Configuration for CronForge."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# Cron field boundaries
CRON_FIELDS = {
    "minute": {"min": 0, "max": 59},
    "hour": {"min": 0, "max": 23},
    "day": {"min": 1, "max": 31},
    "month": {"min": 1, "max": 12},
    "weekday": {"min": 0, "max": 6},  # 0 = Sunday
}

# Day name mappings (for natural language parsing)
DAY_NAMES = {
    "sunday": 0, "sun": 0,
    "monday": 1, "mon": 1,
    "tuesday": 2, "tue": 2,
    "wednesday": 3, "wed": 3,
    "thursday": 4, "thu": 4,
    "friday": 5, "fri": 5,
    "saturday": 6, "sat": 6,
}

# Month name mappings
MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

# Weekday labels for explanation output
WEEKDAY_LABELS = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}

# Common presets
PRESETS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "hourly": "0 * * * *",
    "every_2_hours": "0 */2 * * *",
    "daily_midnight": "0 0 * * *",
    "daily_noon": "0 12 * * *",
    "weekly_sunday": "0 0 * * 0",
    "weekly_monday": "0 0 * * 1",
    "weekdays_9am": "0 9 * * 1-5",
    "monthly_first": "0 0 1 * *",
    "yearly": "0 0 1 1 *",
}


@dataclass
class CronForgeConfig:
    """Runtime configuration for CronForge."""

    timezone: str = field(
        default_factory=lambda: os.getenv("CRONFORGE_TIMEZONE", "UTC")
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("CRONFORGE_LOG_LEVEL", "INFO")
    )
    max_simulation_results: int = field(
        default_factory=lambda: int(
            os.getenv("CRONFORGE_MAX_SIMULATION_RESULTS", "1000")
        )
    )
