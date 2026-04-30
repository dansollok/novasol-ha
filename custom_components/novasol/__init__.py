"""Novasol integration."""
from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .api import NovaSolApiClient
from .const import (
    CONF_PROPERTY_ID,
    CONF_UNIT_ID,
    DOMAIN,
)
from .coordinator import NovaSolCoordinator, NovaSolStatsCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Use a dedicated session (not the shared HA session) so that the login
    # response cookies (accessToken, idToken, expiresAt, …) are stored in a
    # private jar and sent automatically on every subsequent request —
    # including the /awaze-owner-login SSO bridge which needs them all.
    session = aiohttp.ClientSession()

    client = NovaSolApiClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    # Always do a full login on startup so the server sets all auth cookies
    # (accessToken, idToken, expiresAt, …) in our private jar.  The SSO bridge
    # for /novasol/api/ endpoints requires ALL of these to be present.
    await client.authenticate()

    coordinator = NovaSolCoordinator(
        hass,
        entry,
        client,
        property_id=entry.data[CONF_PROPERTY_ID],
        unit_id=entry.data[CONF_UNIT_ID],
    )
    await coordinator.async_config_entry_first_refresh()

    stats_coordinator = NovaSolStatsCoordinator(
        hass,
        entry,
        client,
        property_id=entry.data[CONF_PROPERTY_ID],
    )
    await stats_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "bookings": coordinator,
        "stats":    stats_coordinator,
        "session":  session,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        data = hass.data[DOMAIN].pop(entry.entry_id, {})
        await data["session"].close()
    return unloaded
