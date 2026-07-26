"""Config flow for the MVG integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig
from mvg import MvgApi, TransportType

from .const import (
    CONF_DESTINATIONS,
    CONF_LINES,
    CONF_NUMBER,
    CONF_PRODUCTS,
    CONF_STATION,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_TIMEOFFSET,
    DEFAULT_DESTINATIONS,
    DEFAULT_LINES,
    DEFAULT_NUMBER,
    DEFAULT_PRODUCTS,
    DEFAULT_TIMEOFFSET,
    DOMAIN,
)

ALL_PRODUCTS = [product.value[0] for product in TransportType.all()]


def _csv_to_list(value: str) -> list[str]:
    """Convert a comma-separated string to a list, matching the legacy YAML behavior."""
    items = [item.strip() for item in value.split(",")]
    return items if items else [""]


def _list_to_csv(value: list[str] | None) -> str:
    """Convert a list back to a comma-separated string for form pre-fill."""
    return ", ".join(value) if value else ""


class MvgConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MVG."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Handle the initial step: search for a station."""
        errors: dict[str, str] = {}
        if user_input is not None:
            station = await MvgApi.station_async(user_input[CONF_STATION])
            if station is None:
                errors["base"] = "invalid_station"
            else:
                await self.async_set_unique_id(station["id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or station["name"],
                    data={
                        CONF_STATION_ID: station["id"],
                        CONF_STATION_NAME: station["name"],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION): str,
                vol.Optional(CONF_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, import_data: dict[str, Any]) -> config_entries.ConfigFlowResult:
        """Import a single `nextdeparture` entry from YAML configuration."""
        station = await MvgApi.station_async(import_data[CONF_STATION])
        if station is None:
            return self.async_abort(reason="invalid_station")

        await self.async_set_unique_id(station["id"])
        self._abort_if_unique_id_configured()

        options = {
            CONF_DESTINATIONS: import_data.get(CONF_DESTINATIONS, DEFAULT_DESTINATIONS),
            CONF_LINES: import_data.get(CONF_LINES, DEFAULT_LINES),
            CONF_PRODUCTS: import_data.get(CONF_PRODUCTS, DEFAULT_PRODUCTS),
            CONF_TIMEOFFSET: import_data.get(CONF_TIMEOFFSET, DEFAULT_TIMEOFFSET),
            CONF_NUMBER: import_data.get(CONF_NUMBER, DEFAULT_NUMBER),
        }
        return self.async_create_entry(
            title=import_data.get(CONF_NAME) or station["name"],
            data={
                CONF_STATION_ID: station["id"],
                CONF_STATION_NAME: station["name"],
            },
            options=options,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MvgOptionsFlowHandler:
        """Create the options flow."""
        return MvgOptionsFlowHandler()


class MvgOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle MVG options: destinations, lines, products, timeoffset and number."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            options = {
                CONF_DESTINATIONS: _csv_to_list(user_input[CONF_DESTINATIONS]),
                CONF_LINES: _csv_to_list(user_input[CONF_LINES]),
                CONF_PRODUCTS: user_input.get(CONF_PRODUCTS) or None,
                CONF_TIMEOFFSET: user_input[CONF_TIMEOFFSET],
                CONF_NUMBER: user_input[CONF_NUMBER],
            }
            return self.async_create_entry(data=options)

        current = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_DESTINATIONS,
                    default=_list_to_csv(current.get(CONF_DESTINATIONS, DEFAULT_DESTINATIONS)),
                ): str,
                vol.Optional(
                    CONF_LINES,
                    default=_list_to_csv(current.get(CONF_LINES, DEFAULT_LINES)),
                ): str,
                vol.Optional(
                    CONF_PRODUCTS,
                    default=current.get(CONF_PRODUCTS) or [],
                ): SelectSelector(
                    SelectSelectorConfig(options=ALL_PRODUCTS, multiple=True)
                ),
                vol.Optional(
                    CONF_TIMEOFFSET,
                    default=current.get(CONF_TIMEOFFSET, DEFAULT_TIMEOFFSET),
                ): int,
                vol.Optional(
                    CONF_NUMBER,
                    default=current.get(CONF_NUMBER, DEFAULT_NUMBER),
                ): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
