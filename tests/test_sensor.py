"""Tests for sensor value_fn lambdas."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

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
    "nights":            7,
    "guest_name":        "Anna Schmidt",
    "guest_nationality": "D",
    "adults":            2,
    "children":          0,
    "pets":              0,
    "owner_income_dkk":  5000,
    "is_owner_block":    False,
}

_NOW = datetime.now(timezone.utc)

DATA_WITH_BOOKING = {
    "next_booking":   NEXT_BOOKING,
    "upcoming_count": 3,
    "ytd_income_dkk": 15000,
    "is_occupied":    False,
    "last_poll":      _NOW,
}

DATA_EMPTY = {
    "next_booking":   None,
    "upcoming_count": 0,
    "ytd_income_dkk": 0,
    "is_occupied":    False,
    "last_poll":      None,
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


# ── next_guest_nationality ────────────────────────────────────────────────────

def test_next_guest_nationality_raw_code():
    assert _value("next_guest_nationality", DATA_WITH_BOOKING) == "D"


def test_next_guest_nationality_none_when_no_booking():
    assert _value("next_guest_nationality", DATA_EMPTY) is None


# ── next_guest_country ────────────────────────────────────────────────────────

def test_next_guest_country_maps_to_full_name():
    assert _value("next_guest_country", DATA_WITH_BOOKING) == "Germany"


def test_next_guest_country_unknown_code_falls_back_to_raw():
    booking = {**NEXT_BOOKING, "guest_nationality": "XX"}
    data = {**DATA_WITH_BOOKING, "next_booking": booking}
    assert _value("next_guest_country", data) == "XX"


def test_next_guest_country_none_when_no_booking():
    assert _value("next_guest_country", DATA_EMPTY) is None


# ── next_booking_nights ───────────────────────────────────────────────────────

def test_next_booking_nights():
    booking = {**NEXT_BOOKING, "nights": 7}
    data = {**DATA_WITH_BOOKING, "next_booking": booking}
    assert _value("next_booking_nights", data) == 7


def test_next_booking_nights_none_when_no_booking():
    assert _value("next_booking_nights", DATA_EMPTY) is None


# ── next_booking_adults/children/pets ────────────────────────────────────────

def test_next_booking_adults():
    assert _value("next_booking_adults", DATA_WITH_BOOKING) == 2


def test_next_booking_children():
    assert _value("next_booking_children", DATA_WITH_BOOKING) == 0


def test_next_booking_pets():
    assert _value("next_booking_pets", DATA_WITH_BOOKING) == 0


def test_next_booking_party_none_when_no_booking():
    assert _value("next_booking_adults",   DATA_EMPTY) is None
    assert _value("next_booking_children", DATA_EMPTY) is None
    assert _value("next_booking_pets",     DATA_EMPTY) is None


# ── next_booking_income ───────────────────────────────────────────────────────

def test_next_booking_income():
    assert _value("next_booking_income", DATA_WITH_BOOKING) == 5000


def test_next_booking_income_none_when_no_booking():
    assert _value("next_booking_income", DATA_EMPTY) is None


# ── last_poll ─────────────────────────────────────────────────────────────────

def test_last_poll_returns_datetime():
    val = _value("last_poll", DATA_WITH_BOOKING)
    assert val == _NOW


def test_last_poll_none_before_first_successful_fetch():
    assert _value("last_poll", DATA_EMPTY) is None
