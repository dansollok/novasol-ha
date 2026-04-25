"""Novasol binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NovaSolCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NovaSolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NovaSolOccupiedSensor(coordinator, entry)])


class NovaSolOccupiedSensor(CoordinatorEntity[NovaSolCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Occupied"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator: NovaSolCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_occupied"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Novasol / Awaze",
        }

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("is_occupied", False)

    @property
    def extra_state_attributes(self) -> dict:
        booking = self.coordinator.data.get("occupied_booking")
        if not booking:
            return {}
        return {
            "guest_name":      booking.get("guest_name"),
            "check_in":        booking.get("check_in"),
            "check_out":       booking.get("check_out"),
            "nights":          booking.get("nights"),
            "adults":          booking.get("adults"),
            "children":        booking.get("children"),
            "booking_id":      booking.get("booking_id"),
        }
