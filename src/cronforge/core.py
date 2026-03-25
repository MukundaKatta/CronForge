"""CronForge core — generate, parse, validate, explain, and simulate cron expressions."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel, field_validator

from cronforge.config import (
    CRON_FIELDS,
    PRESETS,
    WEEKDAY_LABELS,
    CronForgeConfig,
)
from cronforge.utils import (
    expand_cron,
    explain_field,
    match_natural_language,
    matches_cron,
    next_matching_times,
    parse_cron_field,
    validate_cron_field,
)


# ---------------------------------------------------------------------------
# Pydantic model for a parsed cron expression
# ---------------------------------------------------------------------------

class CronExpression(BaseModel):
    """Structured representation of a five-field cron expression."""

    minute: str
    hour: str
    day: str
    month: str
    weekday: str

    @field_validator("minute")
    @classmethod
    def _validate_minute(cls, v: str) -> str:
        if not validate_cron_field(v, "minute"):
            raise ValueError(f"Invalid minute field: {v}")
        return v

    @field_validator("hour")
    @classmethod
    def _validate_hour(cls, v: str) -> str:
        if not validate_cron_field(v, "hour"):
            raise ValueError(f"Invalid hour field: {v}")
        return v

    @field_validator("day")
    @classmethod
    def _validate_day(cls, v: str) -> str:
        if not validate_cron_field(v, "day"):
            raise ValueError(f"Invalid day field: {v}")
        return v

    @field_validator("month")
    @classmethod
    def _validate_month(cls, v: str) -> str:
        if not validate_cron_field(v, "month"):
            raise ValueError(f"Invalid month field: {v}")
        return v

    @field_validator("weekday")
    @classmethod
    def _validate_weekday(cls, v: str) -> str:
        if not validate_cron_field(v, "weekday"):
            raise ValueError(f"Invalid weekday field: {v}")
        return v

    def to_string(self) -> str:
        """Return the standard five-field cron string."""
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"

    def __str__(self) -> str:
        return self.to_string()


# ---------------------------------------------------------------------------
# Main CronForge class
# ---------------------------------------------------------------------------

class CronForge:
    """Smart cron job generator — create, validate, explain, and simulate cron schedules.

    Examples
    --------
    >>> cf = CronForge()
    >>> cf.from_natural("every 5 minutes")
    '*/5 * * * *'
    >>> cf.validate("0 9 * * 1-5")
    True
    >>> cf.explain("0 9 * * 1-5")
    'At 09:00, Monday through Friday'
    """

    def __init__(self, config: Optional[CronForgeConfig] = None) -> None:
        self.config = config or CronForgeConfig()

    # ------------------------------------------------------------------
    # Natural language -> cron
    # ------------------------------------------------------------------

    def from_natural(self, description: str) -> str:
        """Convert a natural-language scheduling description to a cron expression.

        Parameters
        ----------
        description : str
            Human-readable schedule, e.g. "every 5 minutes", "daily at 3pm".

        Returns
        -------
        str
            A valid five-field cron expression.

        Raises
        ------
        ValueError
            If the description cannot be matched to any known pattern.
        """
        result = match_natural_language(description)
        if result is None:
            raise ValueError(
                f"Could not parse natural-language description: '{description}'. "
                "Try phrases like 'every 5 minutes', 'daily at 3pm', "
                "'every Monday at 9am', or 'first of every month'."
            )
        return result

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def parse(self, cron_expr: str) -> CronExpression:
        """Parse a cron expression string into a structured ``CronExpression``.

        Parameters
        ----------
        cron_expr : str
            A standard five-field cron expression.

        Returns
        -------
        CronExpression
        """
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"Cron expression must have exactly 5 fields, got {len(parts)}: '{cron_expr}'"
            )
        return CronExpression(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            weekday=parts[4],
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, cron_expr: str) -> bool:
        """Return ``True`` if *cron_expr* is a syntactically valid five-field cron expression."""
        try:
            self.parse(cron_expr)
            return True
        except (ValueError, Exception):
            return False

    # ------------------------------------------------------------------
    # Next runs
    # ------------------------------------------------------------------

    def next_runs(
        self,
        cron_expr: str,
        count: int = 5,
        start: Optional[datetime] = None,
    ) -> List[datetime]:
        """Compute the next *count* run times for a cron expression.

        Parameters
        ----------
        cron_expr : str
            Five-field cron expression.
        count : int
            Number of upcoming run times to return (default 5).
        start : datetime, optional
            Reference point; defaults to now (UTC).

        Returns
        -------
        list[datetime]
        """
        return next_matching_times(cron_expr, count=count, start=start)

    # ------------------------------------------------------------------
    # Explain
    # ------------------------------------------------------------------

    def explain(self, cron_expr: str) -> str:
        """Return a human-readable explanation of a cron expression.

        Parameters
        ----------
        cron_expr : str
            Five-field cron expression.

        Returns
        -------
        str
        """
        parsed = self.parse(cron_expr)

        # Build time component
        if parsed.minute == "*" and parsed.hour == "*":
            time_part = "Every minute"
        elif parsed.minute.startswith("*/"):
            time_part = f"Every {parsed.minute[2:]} minutes"
        elif parsed.hour == "*":
            time_part = f"At minute {parsed.minute} of every hour"
        elif parsed.hour.startswith("*/"):
            step = parsed.hour[2:]
            time_part = f"At minute {parsed.minute}, every {step} hours"
        else:
            time_part = f"At {int(parsed.hour):02d}:{int(parsed.minute):02d}"

        # Build day/month/weekday constraints
        constraints: List[str] = []

        if parsed.day != "*":
            constraints.append(f"on day {parsed.day} of the month")

        if parsed.month != "*":
            constraints.append(f"in month {parsed.month}")

        if parsed.weekday != "*":
            weekday_desc = explain_field(parsed.weekday, "weekday")
            constraints.append(weekday_desc)

        if constraints:
            return f"{time_part}, {', '.join(constraints)}"
        return time_part

    # ------------------------------------------------------------------
    # Cron -> natural language
    # ------------------------------------------------------------------

    def to_natural(self, cron_expr: str) -> str:
        """Convert a cron expression back to a natural-language description.

        This is a best-effort reverse mapping. Complex expressions fall back
        to the structured ``explain()`` output.

        Parameters
        ----------
        cron_expr : str
            Five-field cron expression.

        Returns
        -------
        str
        """
        parsed = self.parse(cron_expr)
        m, h, d, mo, w = parsed.minute, parsed.hour, parsed.day, parsed.month, parsed.weekday

        # Every minute
        if cron_expr.strip() == "* * * * *":
            return "Every minute"

        # Every N minutes
        if m.startswith("*/") and h == "*" and d == "*" and mo == "*" and w == "*":
            return f"Every {m[2:]} minutes"

        # Every N hours
        if m == "0" and h.startswith("*/") and d == "*" and mo == "*" and w == "*":
            return f"Every {h[2:]} hours"

        # Hourly
        if h == "*" and d == "*" and mo == "*" and w == "*" and m != "*":
            if m == "0":
                return "Every hour"
            return f"Every hour at :{int(m):02d}"

        # Daily
        if d == "*" and mo == "*" and w == "*":
            hour_val = int(h)
            minute_val = int(m)
            period = "AM" if hour_val < 12 else "PM"
            display_hour = hour_val % 12 or 12
            if minute_val == 0:
                return f"Daily at {display_hour}{period}"
            return f"Daily at {display_hour}:{minute_val:02d}{period}"

        # Weekdays
        if d == "*" and mo == "*" and w == "1-5":
            hour_val = int(h)
            minute_val = int(m)
            period = "AM" if hour_val < 12 else "PM"
            display_hour = hour_val % 12 or 12
            if minute_val == 0:
                return f"Weekdays at {display_hour}{period}"
            return f"Weekdays at {display_hour}:{minute_val:02d}{period}"

        # Specific weekday
        if d == "*" and mo == "*" and w.isdigit():
            day_name = WEEKDAY_LABELS.get(int(w), f"day {w}")
            hour_val = int(h)
            minute_val = int(m)
            period = "AM" if hour_val < 12 else "PM"
            display_hour = hour_val % 12 or 12
            if minute_val == 0:
                return f"Every {day_name} at {display_hour}{period}"
            return f"Every {day_name} at {display_hour}:{minute_val:02d}{period}"

        # First of every month
        if d == "1" and mo == "*" and w == "*":
            if m == "0" and h == "0":
                return "First of every month at midnight"
            hour_val = int(h)
            minute_val = int(m)
            period = "AM" if hour_val < 12 else "PM"
            display_hour = hour_val % 12 or 12
            return f"First of every month at {display_hour}:{minute_val:02d}{period}"

        # Fallback to explain
        return self.explain(cron_expr)

    # ------------------------------------------------------------------
    # Simulate
    # ------------------------------------------------------------------

    def simulate(
        self,
        cron_expr: str,
        start: datetime,
        end: datetime,
    ) -> List[datetime]:
        """Simulate all cron run times between *start* and *end*.

        Parameters
        ----------
        cron_expr : str
            Five-field cron expression.
        start : datetime
            Simulation start (inclusive).
        end : datetime
            Simulation end (inclusive).

        Returns
        -------
        list[datetime]
        """
        max_count = self.config.max_simulation_results
        return next_matching_times(cron_expr, count=max_count, start=start, end=end)

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    def common_presets(self) -> Dict[str, str]:
        """Return a dictionary of commonly used cron presets.

        Returns
        -------
        dict[str, str]
            Mapping of preset name to cron expression.
        """
        return dict(PRESETS)
