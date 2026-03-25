"""Tests for CronForge core functionality."""

from datetime import datetime

import pytest

from cronforge import CronForge, CronExpression


@pytest.fixture
def cf():
    return CronForge()


# ---------------------------------------------------------------------------
# from_natural
# ---------------------------------------------------------------------------

class TestFromNatural:
    def test_every_minute(self, cf):
        assert cf.from_natural("every minute") == "* * * * *"

    def test_every_n_minutes(self, cf):
        assert cf.from_natural("every 5 minutes") == "*/5 * * * *"
        assert cf.from_natural("every 15 minutes") == "*/15 * * * *"

    def test_every_hour(self, cf):
        assert cf.from_natural("every hour") == "0 * * * *"

    def test_every_n_hours(self, cf):
        assert cf.from_natural("every 2 hours") == "0 */2 * * *"

    def test_daily_at(self, cf):
        assert cf.from_natural("daily at 3pm") == "0 15 * * *"
        assert cf.from_natural("daily at midnight") == "0 0 * * *"
        assert cf.from_natural("daily at noon") == "0 12 * * *"

    def test_every_weekday_at(self, cf):
        assert cf.from_natural("every Monday at 9am") == "0 9 * * 1"
        assert cf.from_natural("every Sunday at noon") == "0 12 * * 0"

    def test_weekdays_at(self, cf):
        assert cf.from_natural("weekdays at 8:30am") == "30 8 * * 1-5"

    def test_first_of_month(self, cf):
        assert cf.from_natural("first of every month") == "0 0 1 * *"

    def test_hourly_at(self, cf):
        assert cf.from_natural("hourly at :30") == "30 * * * *"

    def test_unknown_phrase_raises(self, cf):
        with pytest.raises(ValueError, match="Could not parse"):
            cf.from_natural("whenever the moon is full")


# ---------------------------------------------------------------------------
# parse & validate
# ---------------------------------------------------------------------------

class TestParseAndValidate:
    def test_parse_standard(self, cf):
        expr = cf.parse("*/5 * * * *")
        assert expr.minute == "*/5"
        assert expr.hour == "*"
        assert expr.to_string() == "*/5 * * * *"

    def test_validate_good(self, cf):
        assert cf.validate("0 9 * * 1-5") is True
        assert cf.validate("*/5 * * * *") is True
        assert cf.validate("0 0 1 1 *") is True

    def test_validate_bad(self, cf):
        assert cf.validate("99 * * * *") is False
        assert cf.validate("not a cron") is False
        assert cf.validate("* * * *") is False  # only 4 fields

    def test_parse_invalid_raises(self, cf):
        with pytest.raises(ValueError):
            cf.parse("only four fields here")


# ---------------------------------------------------------------------------
# next_runs & simulate
# ---------------------------------------------------------------------------

class TestScheduling:
    def test_next_runs_count(self, cf):
        start = datetime(2026, 3, 25, 0, 0)
        runs = cf.next_runs("0 * * * *", count=3, start=start)
        assert len(runs) == 3
        assert all(r.minute == 0 for r in runs)

    def test_next_runs_daily(self, cf):
        start = datetime(2026, 3, 25, 0, 0)
        runs = cf.next_runs("0 9 * * *", count=3, start=start)
        assert len(runs) == 3
        for r in runs:
            assert r.hour == 9
            assert r.minute == 0

    def test_simulate_range(self, cf):
        start = datetime(2026, 3, 25, 0, 0)
        end = datetime(2026, 3, 25, 23, 59)
        runs = cf.simulate("0 */2 * * *", start=start, end=end)
        # Every 2 hours from 0:00..22:00 = 12 runs
        assert len(runs) == 12

    def test_simulate_weekly(self, cf):
        start = datetime(2026, 3, 1, 0, 0)
        end = datetime(2026, 3, 31, 23, 59)
        runs = cf.simulate("0 9 * * 1", start=start, end=end)
        # March 2026: Mondays are 2, 9, 16, 23, 30
        assert len(runs) == 5
        for r in runs:
            assert r.weekday() == 0  # Python weekday: Monday = 0


# ---------------------------------------------------------------------------
# explain & to_natural
# ---------------------------------------------------------------------------

class TestExplainAndToNatural:
    def test_explain_every_5_min(self, cf):
        result = cf.explain("*/5 * * * *")
        assert "5 minutes" in result.lower() or "5" in result

    def test_explain_weekday(self, cf):
        result = cf.explain("0 9 * * 1-5")
        assert "09:00" in result
        assert "Monday" in result
        assert "Friday" in result

    def test_to_natural_every_15_min(self, cf):
        result = cf.to_natural("*/15 * * * *")
        assert result == "Every 15 minutes"

    def test_to_natural_daily(self, cf):
        result = cf.to_natural("0 15 * * *")
        assert "Daily" in result
        assert "3PM" in result

    def test_to_natural_weekday(self, cf):
        result = cf.to_natural("0 9 * * 1")
        assert "Monday" in result


# ---------------------------------------------------------------------------
# presets
# ---------------------------------------------------------------------------

class TestPresets:
    def test_common_presets_not_empty(self, cf):
        presets = cf.common_presets()
        assert len(presets) > 0

    def test_presets_all_valid(self, cf):
        for name, expr in cf.common_presets().items():
            assert cf.validate(expr), f"Preset '{name}' is invalid: {expr}"
