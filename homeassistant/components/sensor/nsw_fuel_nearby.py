import datetime
from typing import List

from homeassistant.components.light import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from homeassistant.components.nsw_fuel import DATA_NSW_FUEL
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

DEPENDENCIES = ["nsw_fuel"]

CONF_RADIUS = 'radius'
CONF_LOCATION = 'location'
CONF_FUEL_TYPES = 'fuel_types'
CONF_BRANDS = 'brands'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_RADIUS): cv.positive_int,
    vol.Required(CONF_FUEL_TYPES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_BRANDS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_LOCATION): vol.Schema({
        vol.Required(CONF_LATITUDE): cv.latitude,
        vol.Required(CONF_LONGITUDE): cv.longitude,
    }, extra=vol.REMOVE_EXTRA),
}, extra=vol.REMOVE_EXTRA)

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(hours=1)


def setup_platform(hass, config, add_devices, discovery_info=None):
    fuel_types = config[CONF_FUEL_TYPES]
    radius = config[CONF_RADIUS]
    location = config.get(CONF_LOCATION)
    brands = config.get(CONF_BRANDS)

    if location is None:
        location = {
            CONF_LATITUDE: config[CONF_LATITUDE],
            CONF_LONGITUDE: config[CONF_LONGITUDE],
        }

    client = hass.data[DATA_NSW_FUEL]
    devices = []
    for fuel_type in fuel_types:
        dev = NearbyPriceSensor(
            client,
            location[CONF_LATITUDE],
            location[CONF_LONGITUDE],
            radius,
            brands,
            fuel_type
        )
        dev.update()
        devices.append(dev)

    add_devices(devices)
    return True


class NearbyPriceSensor(Entity):
    def __init__(self, client, latitude: float, longitude: float, radius: int, brands: List[str], fuel_type: str):
        """Initialize the sensor."""
        self._latitude = latitude
        self._longitude = longitude
        self._radius = radius
        self._client = client
        self._fuel_type = fuel_type
        self._brands = brands
        self._cheapest = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'NSW Fuel Nearby Cheapest {}'.format(self._fuel_type)

    @property
    def state(self):
        """Return the state of the sensor."""
        # print(self._data)
        if self._cheapest is None:
            return None

        return self._cheapest[1].name

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        if self._cheapest is not None:
            station = self._cheapest[1]
            price_info = self._cheapest[0]
            attr['Price'] = '{} ¢/L'.format(price_info.price)
            attr['Brand'] = station.brand
            attr['Fuel Type'] = price_info.fuel_type
            attr['Address'] = station.address
        return attr

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update current conditions."""
        results = self._client.get_fuel_prices_within_radius(
            self._latitude,
            self._longitude,
            self._radius,
            self._fuel_type,
            self._brands,
        )
        self._cheapest = sorted([result for result in results if result[0].fuel_type == self._fuel_type],
                                key=lambda result: result[0].price)[0]
