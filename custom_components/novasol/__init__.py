"""Novasol integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NovaSolApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_PROPERTY_ID,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRY,
    CONF_UNIT_ID,
    DOMAIN,
)
from .coordinator import NovaSolCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = NovaSolApiClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    client.load_tokens(
        access_token=entry.data.get(CONF_ACCESS_TOKEN, ""),
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN, ""),
        expiry=entry.data.get(CONF_TOKEN_EXPIRY, 0.0),
    )

    coordinator = NovaSolCoordinator(
        hass,
        entry,
        client,
        property_id=entry.data[CONF_PROPERTY_ID],
        unit_id=entry.data[CONF_UNIT_ID],
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
