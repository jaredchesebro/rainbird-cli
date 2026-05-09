"""Unit tests for formatting.py — format_frequency and format_duration."""

import datetime
from types import SimpleNamespace

import pytest

from pyrainbird.const import DayOfWeek, ProgramFrequency

from formatting import format_duration, format_frequency


def prog(frequency, days_of_week=None, period=None):
    return SimpleNamespace(
        frequency=frequency,
        days_of_week=days_of_week or set(),
        period=period,
    )


# ── format_frequency: CUSTOM ──────────────────────────────────────────────────

def test_custom_mon_wed_fri():
    p = prog(ProgramFrequency.CUSTOM, {DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY})
    assert format_frequency(p) == "Mon Wed Fri"


def test_custom_day_order_is_sun_through_sat():
    p = prog(ProgramFrequency.CUSTOM, {DayOfWeek.FRIDAY, DayOfWeek.MONDAY, DayOfWeek.SUNDAY})
    assert format_frequency(p) == "Sun Mon Fri"


def test_custom_single_day():
    p = prog(ProgramFrequency.CUSTOM, {DayOfWeek.TUESDAY})
    assert format_frequency(p) == "Tue"


def test_custom_all_days():
    all_days = set(DayOfWeek)
    p = prog(ProgramFrequency.CUSTOM, all_days)
    result = format_frequency(p)
    assert result == "Sun Mon Tue Wed Thu Fri Sat"


def test_custom_no_days():
    p = prog(ProgramFrequency.CUSTOM, set())
    assert format_frequency(p) == "No days set"


# ── format_frequency: CYCLIC ──────────────────────────────────────────────────

def test_cyclic_plural():
    p = prog(ProgramFrequency.CYCLIC, period=3)
    assert format_frequency(p) == "Every 3 days"


def test_cyclic_singular():
    p = prog(ProgramFrequency.CYCLIC, period=1)
    assert format_frequency(p) == "Every 1 day"


def test_cyclic_no_period_defaults_to_1():
    p = prog(ProgramFrequency.CYCLIC, period=None)
    assert format_frequency(p) == "Every 1 day"


# ── format_frequency: ODD / EVEN ──────────────────────────────────────────────

def test_odd_days():
    assert format_frequency(prog(ProgramFrequency.ODD)) == "Odd days"


def test_even_days():
    assert format_frequency(prog(ProgramFrequency.EVEN)) == "Even days"


# ── format_duration ───────────────────────────────────────────────────────────

def test_format_duration_ten_minutes():
    td = datetime.timedelta(minutes=10)
    assert format_duration(td) == "10 min"


def test_format_duration_one_minute():
    assert format_duration(datetime.timedelta(minutes=1)) == "1 min"


def test_format_duration_truncates_seconds():
    assert format_duration(datetime.timedelta(minutes=5, seconds=45)) == "5 min"


def test_format_duration_zero():
    assert format_duration(datetime.timedelta(0)) == "0 min"
