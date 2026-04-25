"""Shared fixtures and helpers for Novasol tests.

HA stubs are registered into sys.modules at import time (top of this file)
so that custom_components.novasol.* can be imported without a running HA
instance.  The stubs are minimal but typed correctly so inheritance and
dataclass introspection work.
"""
from __future__ import annotations

# ── HA stubs — must come before any custom_components imports ─────────────────
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock


def _mod(name: str) -> ModuleType:
    """Create a stub module and register it (and all parent packages)."""
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        key = ".".join(parts[:i])
        if key not in sys.modules:
            sys.modules[key] = ModuleType(key)
    return sys.modules[name]


# -- homeassistant.const -------------------------------------------------------
_const = _mod("homeassistant.const")
_const.CONF_PASSWORD = "password"
_const.CONF_USERNAME = "username"

class _Platform(str, Enum):
    CALENDAR       = "calendar"
    SENSOR         = "sensor"
    BINARY_SENSOR  = "binary_sensor"

_const.Platform = _Platform

# -- homeassistant.core --------------------------------------------------------
_core = _mod("homeassistant.core")

class _HomeAssistant:
    config_entries = MagicMock()

_core.HomeAssistant = _HomeAssistant

# -- homeassistant.config_entries ----------------------------------------------
_ce = _mod("homeassistant.config_entries")

class _ConfigEntry:
    def __init__(self):
        self.entry_id = "test-entry-id"
        self.title    = "Novasol D13051"
        self.data     = {}

class _ConfigFlow:
    def __init_subclass__(cls, *, domain: str = "", **kw):
        super().__init_subclass__(**kw)

    VERSION = 1

    async def async_show_form(self, **kw):
        return kw

    async def async_create_entry(self, **kw):
        return kw

    async def async_set_unique_id(self, uid):
        pass

    def _abort_if_unique_id_configured(self):
        pass

_ce.ConfigEntry   = _ConfigEntry
_ce.ConfigFlow    = _ConfigFlow
_ce.ConfigFlowResult = dict   # type alias

# -- homeassistant.helpers.update_coordinator ----------------------------------
_uc = _mod("homeassistant.helpers.update_coordinator")

class _UpdateFailed(Exception):
    pass

class _DataUpdateCoordinator:
    def __init__(self, hass, logger, *, name, update_interval):
        self.hass            = hass
        self.logger          = logger
        self.name            = name
        self.update_interval = update_interval
        self.data: Any       = None

    async def async_config_entry_first_refresh(self):
        self.data = await self._async_update_data()

    async def _async_update_data(self):  # overridden by subclass
        return {}

class _CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def __class_getitem__(cls, item):
        return cls

_uc.DataUpdateCoordinator = _DataUpdateCoordinator
_uc.CoordinatorEntity     = _CoordinatorEntity
_uc.UpdateFailed          = _UpdateFailed

# -- homeassistant.helpers.aiohttp_client -------------------------------------
_ahc = _mod("homeassistant.helpers.aiohttp_client")
_ahc.async_get_clientsession = MagicMock()

# -- homeassistant.helpers.entity_platform ------------------------------------
_ep = _mod("homeassistant.helpers.entity_platform")
_ep.AddEntitiesCallback = Any

# -- homeassistant.components.calendar ----------------------------------------
_cal = _mod("homeassistant.components.calendar")

@dataclass
class _CalendarEvent:
    summary:     str
    start:       date | datetime
    end:         date | datetime
    description: str | None = None
    location:    str | None = None
    uid:         str | None = None

class _CalendarEntity:
    pass

_cal.CalendarEvent  = _CalendarEvent
_cal.CalendarEntity = _CalendarEntity

# -- homeassistant.components.sensor ------------------------------------------
_sensor_mod = _mod("homeassistant.components.sensor")

class _SensorDeviceClass(str, Enum):
    DATE        = "date"
    TIMESTAMP   = "timestamp"
    MONETARY    = "monetary"

class _SensorStateClass(str, Enum):
    MEASUREMENT       = "measurement"
    TOTAL             = "total"
    TOTAL_INCREASING  = "total_increasing"

@dataclass(frozen=True, kw_only=True)
class _SensorEntityDescription:
    key:                          str  = ""
    name:                         str | None = None
    device_class:                 Any = None
    state_class:                  Any = None
    native_unit_of_measurement:   str | None = None

class _SensorEntity:
    entity_description: Any = None
    native_value:       Any = None

_sensor_mod.SensorDeviceClass       = _SensorDeviceClass
_sensor_mod.SensorStateClass        = _SensorStateClass
_sensor_mod.SensorEntityDescription = _SensorEntityDescription
_sensor_mod.SensorEntity            = _SensorEntity

# -- homeassistant.components.binary_sensor -----------------------------------
_bs = _mod("homeassistant.components.binary_sensor")

class _BinarySensorDeviceClass(str, Enum):
    OCCUPANCY = "occupancy"

class _BinarySensorEntity:
    pass

_bs.BinarySensorDeviceClass = _BinarySensorDeviceClass
_bs.BinarySensorEntity      = _BinarySensorEntity

# -- homeassistant.const.UnitOfTime -------------------------------------------
# Sensor uses UnitOfTime from homeassistant.const
class _UnitOfTime(str, Enum):
    DAYS    = "d"
    HOURS   = "h"
    MINUTES = "min"
    SECONDS = "s"

_const.UnitOfTime = _UnitOfTime

# Voluptuous stub (used by config_flow)
_vol = ModuleType("voluptuous")
_vol.Schema   = lambda x, **kw: x
_vol.Required = lambda x, **kw: x
_vol.In       = lambda x: x
sys.modules.setdefault("voluptuous", _vol)


# ── Test helpers ──────────────────────────────────────────────────────────────

import base64
import json
import time
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest


# ── JWT factory ───────────────────────────────────────────────────────────────

def make_jwt(exp_offset: int = 3600, client_id: str = "testclientid123") -> str:
    header  = _b64({"alg": "RS256", "kid": "test-key"})
    payload = _b64({
        "sub":       "test-user-guid",
        "exp":       int(time.time()) + exp_offset,
        "iss":       "https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_TESTPOOL",
        "client_id": client_id,
        "username":  "owner@example.com",
    })
    return f"{header}.{payload}.fake-sig"


def _b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


# ── Mock aiohttp response ─────────────────────────────────────────────────────

def mock_response(status: int = 200, body: dict | list | None = None) -> MagicMock:
    resp = AsyncMock()
    resp.status = status
    resp.ok = status < 400
    resp.json = AsyncMock(return_value=body if body is not None else {})
    resp.text = AsyncMock(return_value=json.dumps(body) if body else "")
    resp.headers = {"content-type": "application/json"}
    if status >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status}")
    else:
        resp.raise_for_status = MagicMock()
    return resp


@asynccontextmanager
async def _ctx(resp):
    yield resp


def mock_session(*responses) -> MagicMock:
    session = MagicMock()
    _make_side_effect(session.get,  list(responses))
    _make_side_effect(session.post, list(responses))
    return session


def _make_side_effect(method, responses):
    itr = iter(responses)

    def side_effect(*args, **kwargs):
        try:
            resp = next(itr)
        except StopIteration:
            resp = mock_response(200, {})
        return _ctx(resp)

    method.side_effect = side_effect


# ── Sample data ───────────────────────────────────────────────────────────────

LOGIN_RESPONSE = {
    "accessToken":  make_jwt(3600),
    "idToken":      make_jwt(3600),
    "refreshToken": "encrypted-refresh-token",
    "accessTokenExpiresAt": int(time.time()) + 3600,
}

REFRESH_RESPONSE = {
    "accessToken":  make_jwt(3600),
    "refreshToken": "rotated-refresh-token",
}

PROPERTIES_RESPONSE = {
    "siteUser": False,
    "sites": [{
        "siteName": "",
        "siteCode": "",
        "siteId":   "",
        "siteProperties": [{
            "propertyCode": "D13051",
            "propertyId":   "D13051",
            "propertyName": "D13051",
            "ownerType":    "owner",
            "managedProperty": False,
            "link":         "https://www.novasol.dk/p/d13051",
            "thumbnail":    "https://image.novasol.com/pic/100/d13/d13051_main_01.jpg",
            "propertyUnits": [{
                "unitCode":      "D13051/1",
                "unitId":        "1",
                "maximumPets":   0,
                "startDateTime": "2025-01-11T12:00:00.000Z",
                "endDateTime":   "2028-01-08T12:00:00.000Z",
            }],
            "propertyCapacity": {"maxAdults": 5, "maxChildren": 0, "maxInfants": 0},
            "productMarket": "Denmark",
        }],
    }],
}

OWNER_BLOCK = {
    "bookingId":    "1-20260815-20260919-0-OWNER",
    "state":        "Owner",
    "propertyId":   "D13051",
    "propertyCode": "D13051",
    "unitCode":     "D13051/1",
    "unitId":       "1",
    "startDate":    "2026-08-15",
    "endDate":      "2026-09-19",
    "nights":       35,
    "leadGuest":    "",
    "leadGuestNationality": "",
    "adultsCount":  0,
    "combinedChildAndInfantsCount": 0,
    "petsCount":    0,
    "bookedOnDate": "",
    "ownerIncome":  0,
    "ownerChargeAmount": 0,
    "currency":     "",
    "extrasOrdered": False,
}

CUSTOMER_BOOKING = {
    "bookingId":    "010189536",
    "state":        "CustomerWithClean",
    "propertyId":   "D13051",
    "propertyCode": "D13051",
    "unitCode":     "D13051/1",
    "unitId":       "1",
    "startDate":    "2026-07-11",
    "endDate":      "2026-08-01",
    "nights":       21,
    "leadGuest":    "Michael Kliesch",
    "leadGuestNationality": "D",
    "adultsCount":  2,
    "combinedChildAndInfantsCount": 3,
    "petsCount":    0,
    "bookedOnDate": "2026-01-15",
    "ownerIncome":  12172,
    "ownerChargeAmount": 0,
    "currency":     "DKK",
    "extrasOrdered": False,
}

BOOKINGLIST_RESPONSE = {
    "fromDate":   "2026-01-01",
    "toDate":     "2027-12-31",
    "searchBy":   "arrival",
    "searchType": "arrival",
    "hideUnitDisplay": False,
    "bookings":   [OWNER_BLOCK, CUSTOMER_BOOKING],
}
