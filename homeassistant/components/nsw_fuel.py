"""
Support for NSW Fuel.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/nsw-fuel/
"""

# REQUIREMENTS = ['nsw-fuel-api-client==1.0.0']

DOMAIN = 'nsw_fuel'

DATA_NSW_FUEL = DOMAIN

def setup(hass, config):
    """Set up the NSW Fuel component."""
    from nsw_fuel import FuelCheckClient
    hass.data[DATA_NSW_FUEL] = FuelCheckClient()
    return True
