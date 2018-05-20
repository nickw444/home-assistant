import requests
import json

bounds = [
    (-34.04223998761286, 151.04506613932858),
    (-33.95350517088142, 151.15492942057858)
]

resp = requests.get('https://api.onegov.nsw.gov.au/FuelCheckApp/v1/fuel/prices/bylocation', {
    'bottomLeftLatitude': bounds[0][0],
    'bottomLeftLongitude': bounds[0][1],
    'topRightLatitude': bounds[1][0],
    'topRightLongitude': bounds[1][1],
    'fueltype': 'P95',
    'brands=': 'SelectAll'
})
print(resp)
print(resp.text)
print(resp.ok)

f = open('response.json', 'w')
f.write(json.dumps(resp.json(), indent=2))



# Price Trends: Week, Month, Year
# Price Averages: Week, Month, Year

# sensor.nsw_fuel_avg_today_p95         128.4c
# sensor.nsw_fuel_avg_week_p95          128.4c
# sensor.nsw_fuel_avg_month_p95         128.4c
# sensor.nsw_fuel_avg_year_p95          128.4c
# sensor.nsw_fuel_trend        'increasing', 'decreasing'
# sensor.nsw_fuel_trend_month_p95       'increasing', 'decreasing'
# sensor.nsw_fuel_trend_year_p95        'increasing', 'decreasing'
# sensor.nsw_fuel_station_xxx_p95       128.4c
# sensor.nsw_fuel_station_xxx_e10       128.4c
# sensor.nsw_fuel_station_cheapest_p95  'Woolworths Blakehurst'
# sensor.nsw_fuel_station_cheapest_e10  'Woolworths Blakehurst'


"""
sensor:
    - platform: nsw_fuel_station
      station_id: 530
"""


class AverageData:
    def update(self):
        """
        POST https://api.onegov.nsw.gov.au/FuelCheckApp/v1/fuel/prices/trends/
        {"location":{"latitude":-33.8708464,"longitude":151.20732999999998},"fueltypes":[{"code":"E10"}]}
        .Variances[]
        """

class TrendData:
    def update(self):
        pass

class LocationData:
    """
    Requests location based data for fuel stations within a rectangle
    """
    def __init__(self, bounds):
        self._bounds = bounds

    def update(self):
        # https://api.onegov.nsw.gov.au/FuelCheckApp/v1/fuel/prices/bylocation
        # ?bottomLeftLatitude=-38.0778358&bottomLeftLongitude=141.0343206
        # &topRightLatitude=-28.1489042&topRightLongitude=153.4826674
        # &brands=SelectAll
        # &fueltype=P95
        pass


class
