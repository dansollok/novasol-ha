"""Tests for NovaSolApiClient."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from custom_components.novasol.api import AuthError, NovaSolApiClient
from .conftest import (
    BOOKINGLIST_RESPONSE,
    CUSTOMER_BOOKING,
    LOGIN_RESPONSE,
    OWNER_BLOCK,
    PROPERTIES_RESPONSE,
    REFRESH_RESPONSE,
    make_jwt,
    mock_response,
    mock_session,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_client(session, username="owner@example.com", password="secret"):
    return NovaSolApiClient(session, username, password)


# ── authenticate() ────────────────────────────────────────────────────────────

async def test_authenticate_success():
    session = mock_session(mock_response(201, LOGIN_RESPONSE))
    client  = make_client(session)

    await client.authenticate()

    tokens = client.dump_tokens()
    assert tokens["access_token"]  == LOGIN_RESPONSE["accessToken"]
    assert tokens["refresh_token"] == LOGIN_RESPONSE["refreshToken"]
    assert tokens["token_expiry"]  > time.time()


async def test_authenticate_stores_parsed_expiry():
    jwt     = make_jwt(exp_offset=7200)
    session = mock_session(mock_response(201, {**LOGIN_RESPONSE, "accessToken": jwt}))
    client  = make_client(session)

    await client.authenticate()

    # Expiry should be approximately now + 7200 s (within 10 s tolerance)
    assert abs(client.dump_tokens()["token_expiry"] - (time.time() + 7200)) < 10


async def test_authenticate_raises_auth_error_on_400():
    session = mock_session(mock_response(400, {"error": "Bad Request"}))
    client  = make_client(session)

    with pytest.raises(AuthError):
        await client.authenticate()


# ── _refresh_access_token() ───────────────────────────────────────────────────

async def test_refresh_success_returns_true():
    session = mock_session(mock_response(201, REFRESH_RESPONSE))
    client  = make_client(session)
    client.load_tokens("old-access", "old-refresh", time.time() - 1)

    result = await client._refresh_access_token()

    assert result is True
    assert client.dump_tokens()["access_token"]  == REFRESH_RESPONSE["accessToken"]
    assert client.dump_tokens()["refresh_token"] == REFRESH_RESPONSE["refreshToken"]


async def test_refresh_returns_false_on_401():
    session = mock_session(mock_response(401, {}))
    client  = make_client(session)
    client.load_tokens("old", "old-refresh", time.time() - 1)

    result = await client._refresh_access_token()

    assert result is False
    assert client.dump_tokens()["access_token"] == "old"   # unchanged


async def test_refresh_returns_false_on_400():
    session = mock_session(mock_response(400, {}))
    client  = make_client(session)
    client.load_tokens("old", "old-refresh", time.time() - 1)

    assert await client._refresh_access_token() is False


async def test_refresh_rotates_token_when_present():
    session = mock_session(mock_response(201, REFRESH_RESPONSE))
    client  = make_client(session)
    client.load_tokens("old", "old-refresh", 0)

    await client._refresh_access_token()

    assert client.dump_tokens()["refresh_token"] == "rotated-refresh-token"


async def test_refresh_keeps_old_refresh_token_when_not_in_response():
    no_rotation = {"accessToken": make_jwt()}
    session = mock_session(mock_response(201, no_rotation))
    client  = make_client(session)
    client.load_tokens("old", "original-refresh", 0)

    await client._refresh_access_token()

    assert client.dump_tokens()["refresh_token"] == "original-refresh"


# ── ensure_valid_token() ──────────────────────────────────────────────────────

async def test_ensure_valid_token_skips_when_fresh():
    session = mock_session()   # no responses — any call would fail
    client  = make_client(session)
    client.load_tokens("fresh-token", "refresh", time.time() + 9999)

    await client.ensure_valid_token()   # should not call session at all

    session.post.assert_not_called()
    session.get.assert_not_called()


async def test_ensure_valid_token_refreshes_near_expiry():
    session = mock_session(mock_response(201, REFRESH_RESPONSE))
    client  = make_client(session)
    client.load_tokens("stale", "refresh", time.time() + 10)  # within 300 s buffer

    await client.ensure_valid_token()

    assert client.dump_tokens()["access_token"] == REFRESH_RESPONSE["accessToken"]


async def test_ensure_valid_token_falls_back_to_login_when_refresh_fails():
    session = mock_session(
        mock_response(401, {}),              # refresh fails
        mock_response(201, LOGIN_RESPONSE),  # full login succeeds
    )
    client = make_client(session)
    client.load_tokens("stale", "expired-refresh", time.time() - 1)

    await client.ensure_valid_token()

    assert client.dump_tokens()["access_token"] == LOGIN_RESPONSE["accessToken"]


async def test_ensure_valid_token_raises_when_both_fail():
    session = mock_session(
        mock_response(401, {}),  # refresh fails
        mock_response(400, {}),  # login also fails
    )
    client = make_client(session)
    client.load_tokens("stale", "expired", time.time() - 1)

    with pytest.raises(AuthError):
        await client.ensure_valid_token()


# ── load_tokens / dump_tokens round-trip ─────────────────────────────────────

def test_token_round_trip():
    session = mock_session()
    client  = make_client(session)
    client.load_tokens("acc", "ref", 12345.0)

    dumped = client.dump_tokens()
    assert dumped == {"access_token": "acc", "refresh_token": "ref", "token_expiry": 12345.0}


# ── get_properties() ─────────────────────────────────────────────────────────

async def test_get_properties_parses_correctly():
    session = mock_session(mock_response(200, PROPERTIES_RESPONSE))
    client  = make_client(session)

    with patch.object(client, "ensure_valid_token", return_value=None):
        props = await client.get_properties()

    assert len(props) == 1
    p = props[0]
    assert p["property_id"] == "D13051"
    assert p["unit_id"]     == "1"
    assert p["max_adults"]  == 5
    assert "novasol.dk"     in p["link"]
    assert "thumbnail"      in p


# ── get_bookings() ────────────────────────────────────────────────────────────

async def test_get_bookings_returns_parsed_list():
    session = mock_session(mock_response(200, BOOKINGLIST_RESPONSE))
    client  = make_client(session)

    with patch.object(client, "ensure_valid_token", return_value=None):
        bookings = await client.get_bookings("D13051", "1")

    assert len(bookings) == 2


async def test_get_bookings_customer_fields():
    session = mock_session(mock_response(200, BOOKINGLIST_RESPONSE))
    client  = make_client(session)

    with patch.object(client, "ensure_valid_token", return_value=None):
        bookings = await client.get_bookings("D13051", "1")

    customer = next(b for b in bookings if not b["is_owner_block"])
    assert customer["booking_id"]       == "010189536"
    assert customer["guest_name"]       == "Michael Kliesch"
    assert customer["guest_nationality"] == "D"
    assert customer["adults"]           == 2
    assert customer["children"]         == 3
    assert customer["owner_income_dkk"] == 12172
    assert customer["currency"]         == "DKK"
    assert customer["check_in"]         == "2026-07-11"
    assert customer["check_out"]        == "2026-08-01"
    assert customer["is_owner_block"]   is False


async def test_get_bookings_owner_block_fields():
    session = mock_session(mock_response(200, BOOKINGLIST_RESPONSE))
    client  = make_client(session)

    with patch.object(client, "ensure_valid_token", return_value=None):
        bookings = await client.get_bookings("D13051", "1")

    owner = next(b for b in bookings if b["is_owner_block"])
    assert owner["guest_name"]       is None
    assert owner["owner_income_dkk"] is None
    assert owner["is_owner_block"]   is True


async def test_get_bookings_empty_string_fields_normalised_to_none():
    """Empty string guest fields from API should become None, not ''."""
    session = mock_session(mock_response(200, BOOKINGLIST_RESPONSE))
    client  = make_client(session)

    with patch.object(client, "ensure_valid_token", return_value=None):
        bookings = await client.get_bookings("D13051", "1")

    owner = next(b for b in bookings if b["is_owner_block"])
    assert owner["guest_name"]  is None
    assert owner["booked_on"]   is None
    assert owner["currency"]    is None


# ── get_booking_detail() ──────────────────────────────────────────────────────

async def test_get_booking_detail_returns_first_element():
    detail = [{"id": "010189536", "guestName": "Michael Kliesch", "ownerAmount": "12172"}]
    session = mock_session(mock_response(200, detail))
    client  = make_client(session)

    with patch.object(client, "ensure_valid_token", return_value=None):
        result = await client.get_booking_detail("010189536")

    assert result["guestName"] == "Michael Kliesch"


async def test_get_booking_detail_returns_none_on_404():
    session = mock_session(mock_response(404, {}))
    client  = make_client(session)

    with patch.object(client, "ensure_valid_token", return_value=None):
        result = await client.get_booking_detail("nonexistent")

    assert result is None


# ── _parse_expiry() ───────────────────────────────────────────────────────────

def test_parse_expiry_decodes_jwt():
    jwt = make_jwt(exp_offset=1800)
    expiry = NovaSolApiClient._parse_expiry(jwt)
    assert abs(expiry - (time.time() + 1800)) < 5


def test_parse_expiry_falls_back_on_garbage():
    expiry = NovaSolApiClient._parse_expiry("not.a.jwt")
    # Should return ~55 minutes from now (fallback)
    assert abs(expiry - (time.time() + 3300)) < 10
