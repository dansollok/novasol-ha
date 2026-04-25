"""Config flow for Novasol integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AuthError, NovaSolApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_PROPERTY_ID,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRY,
    CONF_UNIT_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class NovaSolConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._username: str = ""
        self._password: str = ""
        self._client: NovaSolApiClient | None = None
        self._properties: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            self._client = NovaSolApiClient(session, self._username, self._password)

            try:
                await self._client.authenticate()
                self._properties = await self._client.get_properties()
            except AuthError:
                errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Novasol login")
                errors["base"] = "unknown"

            if not errors:
                if len(self._properties) == 1:
                    return await self._create_entry(self._properties[0])
                return await self.async_step_select_property()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_select_property(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            prop = next(
                p for p in self._properties
                if p["property_id"] == user_input[CONF_PROPERTY_ID]
            )
            return await self._create_entry(prop)

        options = {p["property_id"]: p["name"] for p in self._properties}
        return self.async_show_form(
            step_id="select_property",
            data_schema=vol.Schema({vol.Required(CONF_PROPERTY_ID): vol.In(options)}),
        )

    async def _create_entry(self, prop: dict) -> ConfigFlowResult:
        await self.async_set_unique_id(f"{DOMAIN}_{prop['property_id']}_{prop['unit_id']}")
        self._abort_if_unique_id_configured()

        tokens = self._client.dump_tokens()
        return self.async_create_entry(
            title=f"Novasol {prop['property_id']}",
            data={
                CONF_USERNAME:      self._username,
                CONF_PASSWORD:      self._password,
                CONF_PROPERTY_ID:   prop["property_id"],
                CONF_UNIT_ID:       prop["unit_id"],
                CONF_ACCESS_TOKEN:  tokens["access_token"],
                CONF_REFRESH_TOKEN: tokens["refresh_token"],
                CONF_TOKEN_EXPIRY:  tokens["token_expiry"],
            },
        )
