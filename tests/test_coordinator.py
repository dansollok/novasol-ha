"""Tests for NovaSolCoordinator data transformations."""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.novasol.coordinator import NovaSolCoordinator


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_booking(
    booking_id: str,
    check_in: date,
    check_out: date,
    is_owner_block: bool = False,
    guest_name: str | None = "Test Guest",
    owner_income: int | None = 5000,
    booked_on: str | None = None,
) -> dict:
    return {
        "booking_id":        booking_id,
        "state":             "Owner" if is_owner_block else "CustomerWithClean",
        "property_id":       "D13051",
        "check_in":          check_in.isoformat(),
        "check_out":         check_out.isoformat(),
        "nights":            (check_out - check_in).days,
        "guest_name":        None if is_owner_block else guest_name,
        "guest_nationality": None if is_owner_block else "D",
        "adults":            0 if is_owner_block else 2,
        "children":          0,
        "pets":              0,
        "booked_on":         booked_on,
        "owner_income_dkk":  None if is_owner_block else owner_income,
        "currency":          None if is_owner_block else "DKK",
        "is_owner_block":    is_owner_block,
        "extras_ordered":    False,
    }


def make_coordinator(bookings: list[dict]) -> NovaSolCoordinator:
    hass   = MagicMock()
    entry  = MagicMock()
    entry.data = {
        "access_token":  "tok",
        "refresh_token": "ref",
        "token_expiry":  0,
    }
    client = MagicMock()
    client.get_bookings  = AsyncMock(return_value=bookings)
    client.dump_tokens   = MagicMock(return_value={"access_token": "tok", "refresh_token": "ref", "token_expiry": 0})

    coord = NovaSolCoordinator(hass, entry, client, "D13051", "1")
    return coord


# ── _async_update_data ────────────────────────────────────────────────────────

async def test_update_separates_customer_and_owner_blocks():
    today = date.today()
    bookings = [
        make_booking("OWNER1", today + timedelta(days=10), today + timedelta(days=20), is_owner_block=True),
        make_booking("CUST1",  today + timedelta(days=30), today + timedelta(days=37)),
    ]
    coord = make_coordinator(bookings)

    data = await coord._async_update_data()

    assert len(data["customer"])     == 1
    assert len(data["owner_blocks"]) == 1
    assert len(data["bookings"])     == 2


async def test_update_next_booking_is_soonest_future_customer():
    today = date.today()
    bookings = [
        make_booking("CUST2", today + timedelta(days=60), today + timedelta(days=67)),
        make_booking("CUST1", today + timedelta(days=10), today + timedelta(days=17)),
    ]
    coord = make_coordinator(bookings)

    data = await coord._async_update_data()

    assert data["next_booking"]["booking_id"] == "CUST1"


async def test_update_no_next_booking_when_all_past():
    today = date.today()
    bookings = [
        make_booking("CUST1", today - timedelta(days=20), today - timedelta(days=13)),
    ]
    coord = make_coordinator(bookings)

    data = await coord._async_update_data()

    assert data["next_booking"] is None


async def test_update_is_occupied_true_when_guest_checked_in():
    today = date.today()
    bookings = [
        make_booking("CUST1", today - timedelta(days=2), today + timedelta(days=5)),
    ]
    coord = make_coordinator(bookings)

    data = await coord._async_update_data()

    assert data["is_occupied"] is True
    assert data["occupied_booking"]["booking_id"] == "CUST1"


async def test_update_is_occupied_false_when_nobody_checked_in():
    today = date.today()
    bookings = [
        make_booking("CUST1", today + timedelta(days=5), today + timedelta(days=12)),
    ]
    coord = make_coordinator(bookings)

    data = await coord._async_update_data()

    assert data["is_occupied"] is False
    assert data["occupied_booking"] is None


async def test_update_owner_block_not_counted_as_occupied():
    today = date.today()
    bookings = [
        make_booking("OWN1", today - timedelta(days=2), today + timedelta(days=5), is_owner_block=True),
    ]
    coord = make_coordinator(bookings)

    data = await coord._async_update_data()

    assert data["is_occupied"] is False


async def test_update_ytd_income_sums_current_year_bookings():
    this_year = str(date.today().year)
    last_year = str(date.today().year - 1)
    today = date.today()

    bookings = [
        make_booking("C1", today + timedelta(days=30), today + timedelta(days=37),
                     owner_income=3000, booked_on=f"{this_year}-01-15"),
        make_booking("C2", today + timedelta(days=60), today + timedelta(days=67),
                     owner_income=5000, booked_on=f"{this_year}-03-01"),
        make_booking("C3", today + timedelta(days=90), today + timedelta(days=97),
                     owner_income=2000, booked_on=f"{last_year}-12-01"),  # last year
    ]
    coord = make_coordinator(bookings)

    data = await coord._async_update_data()

    assert data["ytd_income_dkk"] == 8000  # only this year's bookings


async def test_update_upcoming_count_excludes_past_and_current():
    today = date.today()
    bookings = [
        make_booking("PAST",    today - timedelta(days=10), today - timedelta(days=3)),
        make_booking("CURRENT", today - timedelta(days=2),  today + timedelta(days=5)),
        make_booking("FUTURE1", today + timedelta(days=10), today + timedelta(days=17)),
        make_booking("FUTURE2", today + timedelta(days=30), today + timedelta(days=37)),
    ]
    coord = make_coordinator(bookings)

    data = await coord._async_update_data()

    # CURRENT still has check_out in future so counts; PAST does not
    assert data["upcoming_count"] == 3


async def test_update_empty_bookings():
    coord = make_coordinator([])

    data = await coord._async_update_data()

    assert data["customer"]     == []
    assert data["owner_blocks"] == []
    assert data["next_booking"] is None
    assert data["is_occupied"]  is False
    assert data["ytd_income_dkk"] == 0
    assert data["upcoming_count"] == 0
