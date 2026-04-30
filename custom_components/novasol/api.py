"""Novasol API client — pure aiohttp, no browser dependency."""
from __future__ import annotations

import base64
import json
import logging
import time
from datetime import date, datetime, timedelta, timezone

import aiohttp

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)

# How many seconds before expiry we proactively refresh
_REFRESH_BUFFER_SECONDS = 300


class AuthError(Exception):
    """Raised when login or refresh fails with bad credentials."""


class NovaSolApiClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._token_expiry: float = 0.0  # unix timestamp

    # ── Token management ──────────────────────────────────────────────────────

    def load_tokens(self, access_token: str, refresh_token: str, expiry: float) -> None:
        """Restore tokens persisted in the config entry."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expiry = expiry

    def dump_tokens(self) -> dict:
        """Return tokens for persistence in the config entry."""
        return {
            "access_token":  self._access_token,
            "refresh_token": self._refresh_token,
            "token_expiry":  self._token_expiry,
        }

    def _token_needs_refresh(self) -> bool:
        return time.time() > self._token_expiry - _REFRESH_BUFFER_SECONDS

    @staticmethod
    def _parse_expiry(access_token: str) -> float:
        """Decode the JWT payload (no signature verification needed) to get exp."""
        try:
            parts = access_token.split(".")
            payload = parts[1] + "=" * (-len(parts[1]) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload))
            return float(claims["exp"])
        except Exception:
            # Fall back to 55 minutes from now
            return time.time() + 3300

    async def authenticate(self) -> None:
        """Full login with username + password. Raises AuthError on bad credentials."""
        async with self._session.post(
            f"{BASE_URL}/api/auth/login?locale=da",
            json={"username": self._username, "password": self._password},
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status == 400:
                raise AuthError("Invalid username or password")
            resp.raise_for_status()
            data = await resp.json()

        self._access_token = data["accessToken"]
        self._refresh_token = data["refreshToken"]
        self._token_expiry = self._parse_expiry(self._access_token)
        _LOGGER.debug("Full re-authentication successful, token expires at %s", self._token_expiry)

    async def _refresh_access_token(self) -> bool:
        """Use the refresh token to get a new access token. Returns False if expired."""
        try:
            async with self._session.post(
                f"{BASE_URL}/api/auth/refresh",
                json={
                    "accessToken":  self._access_token,
                    "refreshToken": self._refresh_token,
                },
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status in (400, 401):
                    return False
                resp.raise_for_status()
                data = await resp.json()

            self._access_token = data["accessToken"]
            # Refresh token may be rotated
            if "refreshToken" in data:
                self._refresh_token = data["refreshToken"]
            self._token_expiry = self._parse_expiry(self._access_token)
            _LOGGER.debug("Token refreshed, expires at %s", self._token_expiry)
            return True
        except Exception as exc:
            _LOGGER.warning("Token refresh failed: %s", exc)
            return False

    async def ensure_valid_token(self) -> None:
        """Ensure we have a valid access token; re-authenticates automatically."""
        if not self._token_needs_refresh():
            return
        if self._refresh_token and await self._refresh_access_token():
            return
        _LOGGER.info("Refresh token expired or missing — performing full re-login")
        await self.authenticate()

    # ── API calls ─────────────────────────────────────────────────────────────

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type":  "application/json",
        }

    async def get_properties(self) -> list[dict]:
        """Return the list of properties owned by this account."""
        await self.ensure_valid_token()
        async with self._session.get(
            f"{BASE_URL}/v1/users/properties",
            headers=self._auth_headers(),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        properties = []
        for site in data.get("sites", []):
            for prop in site.get("siteProperties", []):
                for unit in prop.get("propertyUnits", []):
                    properties.append({
                        "property_id":   prop["propertyId"],
                        "unit_id":       unit["unitId"],
                        "name":          prop.get("propertyName", prop["propertyId"]),
                        "link":          prop.get("link", ""),
                        "thumbnail":     prop.get("thumbnail", ""),
                        "max_adults":    prop.get("propertyCapacity", {}).get("maxAdults", 0),
                        "contract_end":  unit.get("endDateTime", ""),
                    })
        return properties

    async def get_bookings(
        self,
        property_id: str,
        unit_id: str = "1",
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict]:
        """Fetch the full booking list for a property."""
        _LOGGER.debug("GET bookinglist %s/%s %s→%s", property_id, unit_id, from_date, to_date)
        await self.ensure_valid_token()

        today = date.today()
        if from_date is None:
            from_date = today.replace(month=1, day=1)
        if to_date is None:
            to_date = (today + timedelta(days=730)).replace(month=12, day=31)

        params = {
            "propertyId": property_id,
            "unitId":     unit_id,
            "fromDate":   from_date.isoformat(),
            "toDate":     to_date.isoformat(),
            "searchBy":   "arrival",
            "searchType": "calendar",
        }
        async with self._session.get(
            f"{BASE_URL}/v1/properties/bookinglist",
            params=params,
            headers=self._auth_headers(),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        return [_parse_booking(b) for b in data.get("bookings", [])]

    async def get_key_figures(self, property_id: str) -> dict:
        """Fetch annual key figures from the Drupal API namespace (cookie auth)."""
        await self.ensure_valid_token()
        async with self._session.get(
            f"{BASE_URL}/novasol/api/key_figures",
            params={"rentalId": property_id},
            headers={"Cookie": f"accessToken={self._access_token}"},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_reviews(self, property_id: str) -> dict:
        """Fetch guest review summary from Feefo via the v1 API."""
        await self.ensure_valid_token()
        async with self._session.get(
            f"{BASE_URL}/v1/properties/{property_id}/customerReviews",
            params={"language": "da"},
            headers=self._auth_headers(),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_booking_detail(self, booking_id: str) -> dict | None:
        """Fetch rich detail for a single customer booking."""
        await self.ensure_valid_token()
        async with self._session.get(
            f"{BASE_URL}/v1/bookings/{booking_id}",
            headers=self._auth_headers(),
        ) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            data = await resp.json()

        return data[0] if data else None


# ── Parsing helpers ───────────────────────────────────────────────────────────

def _parse_booking(raw: dict) -> dict:
    return {
        "booking_id":        raw["bookingId"],
        "state":             raw["state"],
        "property_id":       raw["propertyId"],
        "check_in":          raw["startDate"],
        "check_out":         raw["endDate"],
        "nights":            raw["nights"],
        "guest_name":        raw.get("leadGuest") or None,
        "guest_nationality": raw.get("leadGuestNationality") or None,
        "adults":            raw.get("adultsCount", 0),
        "children":          raw.get("combinedChildAndInfantsCount", 0),
        "pets":              raw.get("petsCount", 0),
        "booked_on":         raw.get("bookedOnDate") or None,
        "owner_income_dkk":  raw.get("ownerIncome") or None,
        "currency":          raw.get("currency") or None,
        "is_owner_block":    raw["state"] == "Owner",
        "extras_ordered":    raw.get("extrasOrdered", False),
    }
