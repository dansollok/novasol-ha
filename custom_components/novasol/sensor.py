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
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN
from .coordinator import NovaSolCoordinator, NovaSolStatsCoordinator

# Vehicle-registration nationality codes used by the Novasol API → full country name
_NATIONALITY: dict[str, str] = {
    "A":   "Austria",
    "B":   "Belgium",
    "CH":  "Switzerland",
    "CZ":  "Czech Republic",
    "D":   "Germany",
    "DK":  "Denmark",
    "E":   "Spain",
    "F":   "France",
    "FIN": "Finland",
    "GB":  "United Kingdom",
    "I":   "Italy",
    "L":   "Luxembourg",
    "N":   "Norway",
    "NL":  "Netherlands",
    "P":   "Portugal",
    "PL":  "Poland",
    "S":   "Sweden",
    "SK":  "Slovakia",
    "USA": "United States",
}


def _next(d: dict) -> dict | None:
    return d.get("next_booking")


@dataclass(frozen=True, kw_only=True)
class NovaSolSensorDescription(SensorEntityDescription):
    value_fn: Any = None


SENSORS: tuple[NovaSolSensorDescription, ...] = (
    NovaSolSensorDescription(
        key="next_checkin",
        name="Next check-in",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: (
            date.fromisoformat(_next(d)["check_in"]) if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_checkout",
        name="Next check-out",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: (
            date.fromisoformat(_next(d)["check_out"]) if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="days_until_checkin",
        name="Days until next check-in",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            (date.fromisoformat(_next(d)["check_in"]) - date.today()).days
            if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_guest",
        name="Next guest",
        value_fn=lambda d: (
            _next(d).get("guest_name") if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_guest_nationality",
        name="Next guest nationality",
        value_fn=lambda d: (
            _next(d).get("guest_nationality") if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_guest_country",
        name="Next guest country",
        value_fn=lambda d: (
            _NATIONALITY.get(_next(d).get("guest_nationality", ""), _next(d).get("guest_nationality"))
            if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_booking_nights",
        name="Next booking nights",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            _next(d).get("nights") if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_booking_adults",
        name="Next booking adults",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            _next(d).get("adults") if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_booking_children",
        name="Next booking children",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            _next(d).get("children") if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_booking_pets",
        name="Next booking pets",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            _next(d).get("pets") if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_booking_income",
        name="Next booking income",
        native_unit_of_measurement="DKK",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            _next(d).get("owner_income_dkk") if _next(d) else None
        ),
    ),
    NovaSolSensorDescription(
        key="current_guest",
        name="Current guest",
        value_fn=lambda d: (
            d["occupied_booking"].get("guest_name") if d.get("occupied_booking") else None
        ),
    ),
    NovaSolSensorDescription(
        key="current_checkout",
        name="Current check-out",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: (
            date.fromisoformat(d["occupied_booking"]["check_out"])
            if d.get("occupied_booking") else None
        ),
    ),
    NovaSolSensorDescription(
        key="current_booking_nights",
        name="Current booking nights",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: (
            d["occupied_booking"].get("nights") if d.get("occupied_booking") else None
        ),
    ),
    NovaSolSensorDescription(
        key="next_booking_booked_on",
        name="Next booking booked on",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: (
            date.fromisoformat(_next(d)["booked_on"])
            if _next(d) and _next(d).get("booked_on") else None
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


STATS_SENSORS: tuple[NovaSolSensorDescription, ...] = (
    NovaSolSensorDescription(
        key="annual_income",
        name="Annual income",
        native_unit_of_measurement="DKK",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("annual_income"),
    ),
    NovaSolSensorDescription(
        key="annual_guest_days",
        name="Annual guest days",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("annual_guest_days"),
    ),
    NovaSolSensorDescription(
        key="annual_electricity",
        name="Annual electricity cost",
        native_unit_of_measurement="DKK",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("annual_electricity"),
    ),
    NovaSolSensorDescription(
        key="annual_occupancy",
        name="Annual occupancy",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("annual_occupancy"),
    ),
    NovaSolSensorDescription(
        key="review_score",
        name="Review score",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("review_score"),
    ),
    NovaSolSensorDescription(
        key="review_count",
        name="Review count",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("review_count"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    booking_coordinator: NovaSolCoordinator      = data["bookings"]
    stats_coordinator:   NovaSolStatsCoordinator = data["stats"]
    entities = [
        NovaSolSensor(booking_coordinator, entry, desc) for desc in SENSORS
    ] + [
        NovaSolSensor(stats_coordinator, entry, desc) for desc in STATS_SENSORS
    ]
    async_add_entities(entities)


class NovaSolSensor(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
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
