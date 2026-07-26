"""DataUpdateCoordinator for the MVG integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from mvg import MvgApi, MvgApiError, TransportType

from .const import DOMAIN, SCAN_INTERVAL
from .messages import fetch_incident_messages

_LOGGER = logging.getLogger(__name__)


@dataclass
class MvgData:
    """Raw departures and incident messages for a station."""

    departures: list[dict[str, Any]]
    messages: list[dict[str, Any]]


class MvgDataUpdateCoordinator(DataUpdateCoordinator[MvgData]):
    """Coordinator that polls departures and incident messages for one station."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        timeoffset: int,
        number: int,
        products: list[str] | None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self._station_id = station_id
        self._timeoffset = timeoffset
        self._number = number
        self._transport_types = (
            [product for product in TransportType if product.value[0] in products]
            if products
            else None
        )

    async def _async_update_data(self) -> MvgData:
        """Fetch departures and incident messages from the MVG API."""
        try:
            departures, messages = await asyncio.gather(
                MvgApi.departures_async(
                    station_id=self._station_id,
                    limit=self._number,
                    offset=self._timeoffset,
                    transport_types=self._transport_types,
                ),
                fetch_incident_messages(),
            )
        except MvgApiError as exc:
            raise UpdateFailed(f"Error communicating with MVG API: {exc}") from exc

        return MvgData(departures=departures, messages=messages)
