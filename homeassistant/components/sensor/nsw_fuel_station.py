import datetime

from homeassistant.components.light import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from homeassistant.components.nsw_fuel import DATA_NSW_FUEL
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

DEPENDENCIES = ["nsw_fuel"]

CONF_STATION_ID = 'station_id'
CONF_STATION_NAME = 'station_name'
CONF_FUEL_TYPES = 'fuel_types'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_STATION_ID): cv.positive_int,
    vol.Required(CONF_STATION_NAME): cv.string,
    vol.Required(CONF_FUEL_TYPES, default=[]): vol.All(cv.ensure_list, [cv.string]),
})

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(hours=1)


def setup_platform(hass, config, add_devices, discovery_info=None):
    station_id = config[CONF_STATION_ID]
    station_name = config[CONF_STATION_NAME]
    fuel_types = config[CONF_FUEL_TYPES]

    client = hass.data[DATA_NSW_FUEL]
    station_data = StationPriceData(client, station_id, station_name)
    station_data.update()

    add_devices([StationPriceSensor(station_data, fuel_type) for fuel_type in fuel_types])
    return True


class StationPriceData(object):
    def __init__(self, client, station_id: int, station_name: str):
        self.station_id = station_id
        self.station_name = station_name

        self._client = client
        self._data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        self._data = self._client.get_fuel_prices_for_station(self.station_id)

    def for_fuel_type(self, fuel_type):
        if self._data is None:
            return None
        return next((x for x in self._data if x.fuel_type == fuel_type), None)


class StationPriceSensor(Entity):
    def __init__(self, station_data: StationPriceData, fuel_type: str):
        """Initialize the sensor."""
        self._station_data = station_data
        self._fuel_type = fuel_type

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'NSW Fuel Station {} {}'.format(self._station_data.station_name, self._fuel_type)

    @property
    def state(self):
        """Return the state of the sensor."""
        price_info = self._station_data.for_fuel_type(self._fuel_type)
        if price_info:
            return price_info.price

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        attr['Station ID'] = self._station_data.station_id
        attr['Station Name'] = self._station_data.station_name
        return attr

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return '¢/L'

    def update(self):
        """Update current conditions."""
        self._station_data.update()
