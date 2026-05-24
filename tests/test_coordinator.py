"""Tests for NovaSolCoordinator data transformations."""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.novasol.coordinator import NovaSolCoordinator, NovaSolStatsCoordinator
from .conftest import KEY_FIGURES_RESPONSE, PROPERTY_DETAIL_RESPONSE, REVIEWS_RESPONSE


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


# ── NovaSolStatsCoordinator ───────────────────────────────────────────────────

def make_stats_coordinator(key_figures=None, reviews=None, kf_exc=None, rev_exc=None, prop_detail=None):
    hass   = MagicMock()
    entry  = MagicMock()
    client = MagicMock()

    if kf_exc:
        client.get_key_figures = AsyncMock(side_effect=kf_exc)
    else:
        client.get_key_figures = AsyncMock(return_value=key_figures or {})

    if rev_exc:
        client.get_reviews = AsyncMock(side_effect=rev_exc)
    else:
        client.get_reviews = AsyncMock(return_value=reviews or {})

    client.get_property_detail = AsyncMock(return_value=prop_detail or {})

    return NovaSolStatsCoordinator(hass, entry, client, "D13051")


async def test_stats_parses_key_figures_for_current_year():
    from datetime import date
    year = str(date.today().year)
    kf = {
        "figures": {
            "hire":        {year: 52745},
            "days":        {year: 68},
            "electricity": {year: 4428},
        },
        "events": {
            "booked": {year: 68},
            "owner":  {year: 211},
            "total":  {year: 365},
        },
    }
    coord = make_stats_coordinator(key_figures=kf)
    data = await coord._async_update_data()

    assert data["annual_income"]      == 52745
    assert data["annual_guest_days"]  == 68
    assert data["annual_electricity"] == 4428
    assert data["annual_occupancy"]   == round(68 / (365 - 211) * 100, 1)


async def test_stats_parses_reviews():
    rev = {"averageScore": 4.5, "numberOfReviews": 10}
    coord = make_stats_coordinator(reviews=rev)
    data = await coord._async_update_data()

    assert data["review_score"] == 4.5
    assert data["review_count"] == 10


async def test_stats_returns_none_on_key_figures_failure():
    coord = make_stats_coordinator(kf_exc=Exception("API down"))
    data = await coord._async_update_data()

    assert data["annual_income"]     is None
    assert data["annual_guest_days"] is None


async def test_stats_returns_none_on_reviews_failure():
    coord = make_stats_coordinator(rev_exc=Exception("API down"))
    data = await coord._async_update_data()

    assert data["review_score"] is None
    assert data["review_count"] is None


async def test_stats_occupancy_none_when_no_available_days():
    year = str(date.today().year)
    kf = {
        "figures": {"hire": {}, "days": {}, "electricity": {}},
        "events":  {"booked": {}, "owner": {year: 365}, "total": {year: 365}},
    }
    coord = make_stats_coordinator(key_figures=kf)
    data = await coord._async_update_data()

    assert data["annual_occupancy"] is None


async def test_stats_empty_response_returns_all_none():
    coord = make_stats_coordinator()
    data = await coord._async_update_data()

    for key in ("annual_income", "annual_guest_days", "annual_electricity",
                "annual_occupancy", "review_score", "review_count"):
        assert data[key] is None


# ── Review category scores ────────────────────────────────────────────────────

async def test_stats_parses_overall_category_scores():
    coord = make_stats_coordinator(reviews=REVIEWS_RESPONSE)
    data = await coord._async_update_data()

    assert data["review_cat_value_for_money"] == 4.0
    assert data["review_cat_location"]        == 4.5
    assert data["review_cat_facilities"]      == 5.0
    assert data["review_cat_comfort"]         == 5.0
    assert data["review_cat_cleanliness"]     == 4.5


async def test_stats_category_scores_none_when_no_categories():
    coord = make_stats_coordinator(reviews={"averageScore": 5, "numberOfReviews": 1})
    data = await coord._async_update_data()

    assert data["review_cat_value_for_money"] is None
    assert data["review_cat_cleanliness"]     is None


# ── Latest review ─────────────────────────────────────────────────────────────

async def test_stats_parses_latest_review():
    coord = make_stats_coordinator(reviews=REVIEWS_RESPONSE)
    data = await coord._async_update_data()

    assert data["latest_review_score"] == 5
    assert data["latest_review_date"]  == "2026-04-26"
    assert "schönes" in data["latest_review_text"]
    assert data["latest_reviewer"]     == "Regula"


async def test_stats_latest_review_none_when_empty_reviews():
    coord = make_stats_coordinator(reviews={"averageScore": 5, "numberOfReviews": 0, "reviews": []})
    data = await coord._async_update_data()

    assert data["latest_review_score"] is None
    assert data["latest_review_date"]  is None
    assert data["latest_review_text"]  is None
    assert data["latest_reviewer"]     is None


async def test_stats_latest_reviewer_none_when_name_is_empty_string():
    """Empty string reviewer name must be normalised to None."""
    review_with_anon = {**REVIEWS_RESPONSE, "reviews": [REVIEWS_RESPONSE["reviews"][1]]}
    coord = make_stats_coordinator(reviews=review_with_anon)
    data = await coord._async_update_data()

    assert data["latest_reviewer"] is None
