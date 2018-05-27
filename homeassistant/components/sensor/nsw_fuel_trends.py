import datetime

from homeassistant.components.light import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from homeassistant.components.nsw_fuel import DATA_NSW_FUEL
from homeassistant.const import CONF_LONGITUDE, CONF_LATITUDE
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

DEPENDENCIES = ["nsw_fuel"]

CONF_LOCATION = 'location'
CONF_FUEL_TYPES = 'fuel_types'
CONF_PERIODS = 'periods'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LOCATION): vol.Schema({
        vol.Required(CONF_LATITUDE): cv.latitude,
        vol.Required(CONF_LONGITUDE): cv.longitude,
    }, extra=vol.REMOVE_EXTRA),
    vol.Required(CONF_FUEL_TYPES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Required(CONF_PERIODS, default=[]): vol.All(cv.ensure_list, [cv.string]),
})

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(hours=1)


def setup_platform(hass, config, add_devices, discovery_info=None):
    from nsw_fuel import Period

    fuel_types = config[CONF_FUEL_TYPES]
    periods = config[CONF_PERIODS]
    location = config.get(CONF_LOCATION)

    if location is None:
        # TODO Fix this.
        location = {
            CONF_LATITUDE: config[CONF_LATITUDE],
            CONF_LONGITUDE: config[CONF_LONGITUDE],
        }

    client = hass.data[DATA_NSW_FUEL]
    trend_data = PriceTrendData(client, location['latitude'], location['longitude'], fuel_types)
    trend_data.update()

    devices = []
    # Create average price sensors
    for fuel_type in fuel_types:
        devices.append(PriceTrendSensor(trend_data, fuel_type))
        for period in periods:
            devices.append(AveragePriceSensor(
                trend_data,
                fuel_type,
                Period(period)
            ))

    add_devices(devices)
    return True


class PriceTrendData(object):
    def __init__(self, client, latitude, longitude, fuel_types):
        self._client = client
        self._latitude = latitude
        self._longitude = longitude
        self._fuel_types = fuel_types

        self.latest_data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        self.latest_data = self._client.get_fuel_price_trends(
            self._latitude,
            self._longitude,
            self._fuel_types
        )


class PriceTrendSensor(Entity):
    """
    A sensor that outputs information regarding the price trend direction
    """

    def __init__(self, trend_data: PriceTrendData, fuel_type: str):
        """Initialize the sensor."""
        self._trend_data = trend_data
        self._fuel_type = fuel_type

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'NSW Fuel {} Trend'.format(self._fuel_type)

    @property
    def state(self):
        """Return the state of the sensor."""
        from nsw_fuel import Period

        average_prices = self._trend_data.latest_data['average_prices']
        average_prices = [x for x in average_prices if x.fuel_type == self._fuel_type and x.period == Period.WEEK]
        average_prices = sorted(average_prices, key=lambda x: x.captured, reverse=True)
        if len(average_prices) > 2:
            if average_prices[0].price > average_prices[1].price:
                return 'Increasing'
            elif average_prices[0].price < average_prices[1].price:
                return 'Decreasing'
            else:
                return 'No Change'

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return {}

    def update(self):
        """Update current conditions."""
        self._trend_data.update()


class AveragePriceSensor(Entity):
    def __init__(self, trend_data: PriceTrendData, fuel_type: str, period):
        """Initialize the sensor."""
        self._trend_data = trend_data
        self._fuel_type = fuel_type
        self._period = period

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'NSW Fuel {} {} Average'.format(self._fuel_type, self._period)

    @property
    def state(self):
        """Return the state of the sensor."""
        variances = self._trend_data.latest_data['variances']

        print(variances)

        average_data = next((x for x in variances if x.period == self._period and x.fuel_type == self._fuel_type), None)
        if average_data is not None:
            return average_data.price

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return {}

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return '¢/L'

    def update(self):
        """Update current conditions."""
        self._trend_data.update()
