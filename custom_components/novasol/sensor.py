"""Novasol sensors."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NovaSolCoordinator


@dataclass(frozen=True, kw_only=True)
class NovaSolSensorDescription(SensorEntityDescription):
    value_fn: Any = None


SENSORS: tuple[NovaSolSensorDescription, ...] = (
    NovaSolSensorDescription(
        key="next_checkin",
        name="Next check-in",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: (
            date.fromisoformat(d["next_booking"]["check_in"])
            if d.get("next_booking") else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_checkout",
        name="Next check-out",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: (
            date.fromisoformat(d["next_booking"]["check_out"])
            if d.get("next_booking") else None
        ),
    ),
    NovaSolSensorDescription(
        key="days_until_checkin",
        name="Days until next check-in",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            (date.fromisoformat(d["next_booking"]["check_in"]) - date.today()).days
            if d.get("next_booking") else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_guest",
        name="Next guest",
        value_fn=lambda d: (
            d["next_booking"].get("guest_name")
            if d.get("next_booking") else None
        ),
    ),
    NovaSolSensorDescription(
        key="upcoming_bookings",
        name="Upcoming bookings",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("upcoming_count", 0),
    ),
    NovaSolSensorDescription(
        key="ytd_income",
        name="Year-to-date income",
        native_unit_of_measurement="DKK",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.get("ytd_income_dkk", 0),
    ),
    NovaSolSensorDescription(
        key="last_poll",
        name="Last successful poll",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.get("last_poll"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NovaSolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NovaSolSensor(coordinator, entry, description) for description in SENSORS
    )


class NovaSolSensor(CoordinatorEntity[NovaSolCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NovaSolCoordinator,
        entry: ConfigEntry,
        description: NovaSolSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Novasol / Awaze",
        }

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)
