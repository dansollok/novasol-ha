"""Tests for calendar entity helpers."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from custom_components.novasol.calendar import _booking_to_event

# ── Sample bookings ───────────────────────────────────────────────────────────

CUSTOMER = {
    "booking_id":        "010189536",
    "is_owner_block":    False,
    "check_in":          "2026-07-11",
    "check_out":         "2026-08-01",
    "guest_name":        "Michael Kliesch",
    "guest_nationality": "D",
    "adults":            2,
    "children":          3,
    "pets":              0,
    "owner_income_dkk":  12172,
    "booked_on":         "2025-12-29",
    "extras_ordered":    False,
}

OWNER = {
    "booking_id":        "1-20260815-20260919-0-OWNER",
    "is_owner_block":    True,
    "check_in":          "2026-08-15",
    "check_out":         "2026-09-19",
    "guest_name":        None,
    "guest_nationality": None,
    "adults":            0,
    "children":          0,
    "pets":              0,
    "owner_income_dkk":  None,
    "booked_on":         None,
    "extras_ordered":    False,
}

# ── _booking_to_event ─────────────────────────────────────────────────────────

def test_customer_event_summary_contains_guest_name():
    event = _booking_to_event(CUSTOMER)
    assert "Michael Kliesch" in event.summary


def test_customer_event_summary_contains_flag_for_german_guest():
    event = _booking_to_event(CUSTOMER)
    assert "🇩🇪" in event.summary


def test_customer_event_summary_has_suitcase_emoji():
    event = _booking_to_event(CUSTOMER)
    assert "🧳" in event.summary


def test_owner_block_summary():
    event = _booking_to_event(OWNER)
    assert "Owner block" in event.summary
    assert "🏡" in event.summary


def test_owner_block_has_no_guest_info_in_description():
    event = _booking_to_event(OWNER)
    assert event.description is None or "Michael" not in (event.description or "")


def test_customer_event_dates():
    event = _booking_to_event(CUSTOMER)
    assert event.start == date(2026, 7, 11)
    assert event.end   == date(2026, 8, 1)


def test_owner_block_dates():
    event = _booking_to_event(OWNER)
    assert event.start == date(2026, 8, 15)
    assert event.end   == date(2026, 9, 19)


def test_customer_event_uid_is_booking_id():
    event = _booking_to_event(CUSTOMER)
    assert event.uid == "010189536"


def test_owner_block_uid_is_booking_id():
    event = _booking_to_event(OWNER)
    assert event.uid == "1-20260815-20260919-0-OWNER"


def test_customer_description_contains_adults():
    event = _booking_to_event(CUSTOMER)
    assert "2 adults" in (event.description or "")


def test_customer_description_contains_children():
    event = _booking_to_event(CUSTOMER)
    assert "3 children" in (event.description or "")


def test_customer_description_contains_income():
    event = _booking_to_event(CUSTOMER)
    assert "12,172" in (event.description or "") or "12172" in (event.description or "")


def test_customer_description_contains_booked_on():
    event = _booking_to_event(CUSTOMER)
    assert "2025-12-29" in (event.description or "")


def test_unknown_nationality_no_flag():
    booking = {**CUSTOMER, "guest_nationality": "XX"}
    event = _booking_to_event(booking)
    # Should not crash; flag just omitted
    assert "Michael Kliesch" in event.summary


def test_no_nationality_no_flag():
    booking = {**CUSTOMER, "guest_nationality": None}
    event = _booking_to_event(booking)
    assert "Michael Kliesch" in event.summary


def test_pets_shown_in_description():
    booking = {**CUSTOMER, "pets": 2}
    event = _booking_to_event(booking)
    assert "2 pets" in (event.description or "")


def test_no_income_omitted_from_description():
    booking = {**CUSTOMER, "owner_income_dkk": None}
    event = _booking_to_event(booking)
    assert "Income" not in (event.description or "")
