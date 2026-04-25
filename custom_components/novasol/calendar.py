"""Novasol calendar entity."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NovaSolCoordinator

# Nationality code → flag emoji for event summaries
_FLAGS = {
    "D": "🇩🇪", "DK": "🇩🇰", "N": "🇳🇴", "S": "🇸🇪",
    "NL": "🇳🇱", "GB": "🇬🇧", "F": "🇫🇷", "CH": "🇨🇭",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NovaSolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NovaSolCalendar(coordinator, entry)])


class NovaSolCalendar(CoordinatorEntity[NovaSolCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Bookings"

    def __init__(self, coordinator: NovaSolCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Novasol / Awaze",
        }

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming booking (what HA shows as 'current event')."""
        next_b = self.coordinator.data.get("next_booking")
        if next_b is None:
            return None
        return _booking_to_event(next_b)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        bookings = self.coordinator.data.get("bookings", [])
        events = []
        for b in bookings:
            check_in  = date.fromisoformat(b["check_in"])
            check_out = date.fromisoformat(b["check_out"])
            # Include if the booking overlaps with the requested window
            if check_out > start_date.date() and check_in < end_date.date():
                events.append(_booking_to_event(b))
        return events


def _booking_to_event(b: dict) -> CalendarEvent:
    if b["is_owner_block"]:
        summary = "🏡 Owner block"
    else:
        nat   = b.get("guest_nationality") or ""
        flag  = _FLAGS.get(nat, "")
        name  = b.get("guest_name") or "Guest"
        summary = f"🧳 {flag} {name}".strip()

    description_parts = []
    if not b["is_owner_block"]:
        parts = []
        if b.get("adults"):
            parts.append(f"{b['adults']} adults")
        if b.get("children"):
            parts.append(f"{b['children']} children")
        if b.get("pets"):
            parts.append(f"{b['pets']} pets")
        if parts:
            description_parts.append(", ".join(parts))
        if b.get("owner_income_dkk"):
            description_parts.append(f"Income: {b['owner_income_dkk']:,} DKK")
        if b.get("booked_on"):
            description_parts.append(f"Booked: {b['booked_on']}")

    return CalendarEvent(
        summary=summary,
        start=date.fromisoformat(b["check_in"]),
        end=date.fromisoformat(b["check_out"]),
        description="\n".join(description_parts) or None,
        uid=b["booking_id"],
    )
