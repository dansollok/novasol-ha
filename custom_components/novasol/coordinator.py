"""DataUpdateCoordinator for Novasol bookings."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import AuthError, NovaSolApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRY,
    DOMAIN,
    SCAN_INTERVAL_HOURS,
    SCAN_INTERVAL_STATS_HOURS,
)

_LOGGER = logging.getLogger(__name__)


class NovaSolCoordinator(DataUpdateCoordinator):
    """Fetches bookings and keeps the token pair in sync with the config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: NovaSolApiClient,
        property_id: str,
        unit_id: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=SCAN_INTERVAL_HOURS),
        )
        self._entry = entry
        self._client = client
        self.property_id = property_id
        self.unit_id = unit_id

    async def _async_update_data(self) -> dict:
        _LOGGER.debug("Fetching bookings for property %s", self.property_id)
        try:
            bookings = await self._client.get_bookings(
                self.property_id,
                self.unit_id,
                from_date=date.today().replace(month=1, day=1),
                to_date=(date.today() + timedelta(days=730)).replace(month=12, day=31),
            )
        except AuthError as exc:
            raise UpdateFailed(f"Authentication failed: {exc}") from exc
        except Exception as exc:
            raise UpdateFailed(f"Error fetching bookings: {exc}") from exc

        customer = [b for b in bookings if not b["is_owner_block"]]
        owner    = [b for b in bookings if     b["is_owner_block"]]
        _LOGGER.debug(
            "Fetched %d bookings (%d customer, %d owner blocks)",
            len(bookings), len(customer), len(owner),
        )

        # Persist any token changes (refresh may have rotated the tokens)
        tokens = self._client.dump_tokens()
        if tokens["access_token"] != self._entry.data.get(CONF_ACCESS_TOKEN):
            _LOGGER.debug("Access token rotated — persisting new tokens to config entry")
            self.hass.config_entries.async_update_entry(
                self._entry,
                data={
                    **self._entry.data,
                    CONF_ACCESS_TOKEN:  tokens["access_token"],
                    CONF_REFRESH_TOKEN: tokens["refresh_token"],
                    CONF_TOKEN_EXPIRY:  tokens["token_expiry"],
                },
            )

        today = date.today()

        # Next upcoming customer booking
        future_customer = sorted(
            [b for b in customer if date.fromisoformat(b["check_out"]) > today],
            key=lambda b: b["check_in"],
        )
        next_booking = future_customer[0] if future_customer else None
        if next_booking:
            _LOGGER.debug(
                "Next booking: %s (%s) checking in %s",
                next_booking.get("guest_name", "unknown"),
                next_booking["booking_id"],
                next_booking["check_in"],
            )
        else:
            _LOGGER.debug("No upcoming customer bookings found")

        # Is the property occupied right now?
        occupied_booking = next(
            (
                b for b in customer
                if date.fromisoformat(b["check_in"]) <= today < date.fromisoformat(b["check_out"])
            ),
            None,
        )
        if occupied_booking:
            _LOGGER.info(
                "Property currently occupied by %s (checkout %s)",
                occupied_booking.get("guest_name", "unknown"),
                occupied_booking["check_out"],
            )

        # YTD income
        ytd_income = sum(
            b["owner_income_dkk"] or 0
            for b in customer
            if b["booked_on"] and b["booked_on"].startswith(str(today.year))
        )
        _LOGGER.debug("YTD income: %d DKK", ytd_income)

        return {
            "bookings":         bookings,
            "customer":         customer,
            "owner_blocks":     owner,
            "next_booking":     next_booking,
            "occupied_booking": occupied_booking,
            "is_occupied":      occupied_booking is not None,
            "ytd_income_dkk":   ytd_income,
            "upcoming_count":   len(future_customer),
            "last_poll":        datetime.now(timezone.utc),
        }


class NovaSolStatsCoordinator(DataUpdateCoordinator):
    """Fetches slowly-changing data: annual key figures and review scores (every 24 h)."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: NovaSolApiClient,
        property_id: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_stats",
            update_interval=timedelta(hours=SCAN_INTERVAL_STATS_HOURS),
        )
        self._client = client
        self.property_id = property_id

    async def _async_update_data(self) -> dict:
        year = str(date.today().year)

        key_figures: dict = {}
        try:
            key_figures = await self._client.get_key_figures(self.property_id)
        except Exception as exc:
            _LOGGER.warning("Failed to fetch key figures: %s", exc)

        reviews: dict = {}
        try:
            reviews = await self._client.get_reviews(self.property_id)
        except Exception as exc:
            _LOGGER.warning("Failed to fetch reviews: %s", exc)

        figures = key_figures.get("figures", {})
        events  = key_figures.get("events", {})

        hire   = figures.get("hire", {})
        days   = figures.get("days", {})
        elec   = figures.get("electricity", {})
        booked = events.get("booked", {})
        owner  = events.get("owner", {})
        total  = events.get("total", {})

        available   = (total.get(year) or 0) - (owner.get(year) or 0)
        booked_days = booked.get(year) or 0
        occupancy   = round(booked_days / available * 100, 1) if available > 0 else None

        return {
            "annual_income":      hire.get(year),
            "annual_guest_days":  days.get(year),
            "annual_electricity": elec.get(year),
            "annual_occupancy":   occupancy,
            "review_score":       reviews.get("averageScore"),
            "review_count":       reviews.get("numberOfReviews"),
        }
