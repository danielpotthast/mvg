"""Support for departure information for public transport in Munich."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
import logging

from .mvgapi import MvgApi, TransportType
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.const import CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.exceptions import ConfigEntryError

_LOGGER = logging.getLogger(__name__)

CONF_NEXT_DEPARTURE = "nextdeparture"
CONF_STATION = "station"
CONF_DESTINATIONS = "destinations"
CONF_LINES = "lines"
CONF_PRODUCTS = "products"
CONF_TIMEOFFSET = "timeoffset"
CONF_NUMBER = "number"

NONE_ICON = "mdi:clock"

ATTRIBUTION = "Data provided by mvg.de"

SCAN_INTERVAL = timedelta(seconds=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NEXT_DEPARTURE): [
            {
                vol.Required(CONF_STATION): cv.string,
                vol.Optional(CONF_DESTINATIONS, default=[""]): cv.ensure_list_csv,
                vol.Optional(CONF_LINES, default=[""]): cv.ensure_list_csv,
                vol.Optional(CONF_PRODUCTS, default=None): cv.ensure_list_csv,
                vol.Optional(CONF_TIMEOFFSET, default=0): cv.positive_int,
                vol.Optional(CONF_NUMBER, default=5): cv.positive_int,
                vol.Optional(CONF_NAME): cv.string,
            }
        ]
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities_callback: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the MVGLive sensor."""
    sensors = []
    for nextdeparture in config[CONF_NEXT_DEPARTURE]:
        station_name = nextdeparture.get(CONF_STATION)
        station_metadata = await MvgApi.station_async(station_name)
        if station_metadata is None:
            raise ConfigEntryError(f"Invalid station name: {station_name}")
        api = MvgApi(station_metadata["id"])
        sensors.append(
            MVGSensor(
                api,
                station_metadata["name"],
                nextdeparture.get(CONF_DESTINATIONS),
                nextdeparture.get(CONF_LINES),
                nextdeparture.get(CONF_PRODUCTS),
                nextdeparture.get(CONF_TIMEOFFSET),
                nextdeparture.get(CONF_NUMBER),
                nextdeparture.get(CONF_NAME),
            )
        )
    async_add_entities_callback(sensors, True)


class MVGSensor(SensorEntity):
    """Implementation of an MVG sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(
        self,
        api,
        station_name,
        destinations,
        lines,
        products,
        timeoffset,
        number,
        name,
    ):
        """Initialize the sensor."""
        self._api = api
        self._station_name = station_name
        self._name = name
        self.data = MVGData(api, destinations, lines, products, timeoffset, number)
        self._state = None
        self._icon = NONE_ICON

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._name:
            return self._name
        return self._station_name

    @property
    def native_value(self):
        """Return the next departure time."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not (dep := self.data.departures):
            return None
        attr = dep[0]  # next departure attributes
        attr["departures"] = deepcopy(dep)  # all departures dictionary
        attr["messages"] = deepcopy(self.data.messages)  # all messages dictionary
        return attr

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    async def async_update(self) -> None:
        """Get the latest data and update the state."""
        await self.data.update()
        if not self.data.departures:
            self._state = None
            self._icon = NONE_ICON
        else:
            self._state = self.data.departures[0].get("time_in_mins", "-")
            self._icon = self.data.departures[0]["icon"]

def _get_minutes_until_departure(departure_time: int) -> int:
    """Calculate the time difference in minutes between the current time and a given departure time.
    Args:
        departure_time: Unix timestamp of the departure time, in seconds.
    Returns:
        The time difference in minutes, as a float.
    """
    current_time = datetime.now()
    departure_datetime = datetime.fromtimestamp(departure_time)
    time_difference = (departure_datetime - current_time).total_seconds()
    minutes_difference = int(time_difference / 60.0)
    return minutes_difference

class MVGData:
    """Pull data from the mvg.de web page."""
    def __init__(self, api, destinations, lines, products, timeoffset, number):
        """Initialize the sensor."""
        self._destinations = destinations
        self._lines = lines
        self._products = products
        self._timeoffset = timeoffset
        self._number = number
        self.mvg = api
        self.departures = []

    async def update(self):
        """Update the connection data."""
        try:
            _departures = await self.mvg.departures_async(
                station_id=self.mvg.station_id,
                offset=self._timeoffset,
                limit=self._number,
                transport_types=[
                    transport_type
                    for transport_type in TransportType
                    if transport_type.value[0] in self._products
                ]
                if self._products
                else None,
            )
        except ValueError:
            self.departures = []
            _LOGGER.warning("Returned data not understood")
            return
        self.departures = []
        for _departure in _departures:
            # find the first departure meeting the criteria
            if (
                "" not in self._destinations[:1]
                and _departure["destination"] not in self._destinations
            ):
                continue

            if "" not in self._lines[:1] and _departure["line"] not in self._lines:
                continue

            time_to_departure = _get_minutes_until_departure(_departure["time"])

            if time_to_departure < self._timeoffset:
                continue

            # now select the relevant data
            _nextdep = {}
            for k in ("destination", "line", "type", "cancelled", "icon", "platform"):
                _nextdep[k] = _departure.get(k, "")
            _nextdep["time_in_mins"] = time_to_departure
            self.departures.append(_nextdep)

        # Fetch messages and store them in the data object
        self.messages = await self.mvg.messages_async()
