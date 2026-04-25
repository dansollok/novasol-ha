"""Tests for sensor value_fn lambdas."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from custom_components.novasol.sensor import SENSORS

# ── Helpers ───────────────────────────────────────────────────────────────────

def _sensor(key: str):
    return next(s for s in SENSORS if s.key == key)


def _value(key: str, data: dict):
    return _sensor(key).value_fn(data)


NEXT_BOOKING = {
    "check_in":          (date.today() + timedelta(days=10)).isoformat(),
    "check_out":         (date.today() + timedelta(days=17)).isoformat(),
    "guest_name":        "Anna Schmidt",
    "owner_income_dkk":  3600,
    "is_owner_block":    False,
}

DATA_WITH_BOOKING = {
    "next_booking":   NEXT_BOOKING,
    "upcoming_count": 3,
    "ytd_income_dkk": 15000,
    "is_occupied":    False,
}

DATA_EMPTY = {
    "next_booking":   None,
    "upcoming_count": 0,
    "ytd_income_dkk": 0,
    "is_occupied":    False,
}

# ── next_checkin ──────────────────────────────────────────────────────────────

def test_next_checkin_returns_date():
    val = _value("next_checkin", DATA_WITH_BOOKING)
    assert val == date.today() + timedelta(days=10)


def test_next_checkin_none_when_no_booking():
    assert _value("next_checkin", DATA_EMPTY) is None


# ── next_checkout ─────────────────────────────────────────────────────────────

def test_next_checkout_returns_date():
    val = _value("next_checkout", DATA_WITH_BOOKING)
    assert val == date.today() + timedelta(days=17)


def test_next_checkout_none_when_no_booking():
    assert _value("next_checkout", DATA_EMPTY) is None


# ── days_until_checkin ────────────────────────────────────────────────────────

def test_days_until_checkin_is_integer():
    val = _value("days_until_checkin", DATA_WITH_BOOKING)
    assert val == 10


def test_days_until_checkin_none_when_no_booking():
    assert _value("days_until_checkin", DATA_EMPTY) is None


def test_days_until_checkin_negative_when_overdue():
    overdue_booking = {**NEXT_BOOKING, "check_in": (date.today() - timedelta(days=3)).isoformat()}
    data = {**DATA_WITH_BOOKING, "next_booking": overdue_booking}
    assert _value("days_until_checkin", data) == -3


# ── next_guest ────────────────────────────────────────────────────────────────

def test_next_guest_returns_name():
    assert _value("next_guest", DATA_WITH_BOOKING) == "Anna Schmidt"


def test_next_guest_none_when_no_booking():
    assert _value("next_guest", DATA_EMPTY) is None


def test_next_guest_none_when_owner_block():
    owner_data = {**DATA_WITH_BOOKING, "next_booking": {**NEXT_BOOKING, "guest_name": None}}
    assert _value("next_guest", owner_data) is None


# ── upcoming_bookings ─────────────────────────────────────────────────────────

def test_upcoming_bookings_count():
    assert _value("upcoming_bookings", DATA_WITH_BOOKING) == 3


def test_upcoming_bookings_zero():
    assert _value("upcoming_bookings", DATA_EMPTY) == 0


# ── ytd_income ────────────────────────────────────────────────────────────────

def test_ytd_income_value():
    assert _value("ytd_income", DATA_WITH_BOOKING) == 15000


def test_ytd_income_zero_when_empty():
    assert _value("ytd_income", DATA_EMPTY) == 0
