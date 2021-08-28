"""Support for Aussie Broadband metric sensors."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.sensor import STATE_CLASS_TOTAL_INCREASING, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DATA_MEGABYTES, DATA_KILOBYTES
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN, SERVICE_ID

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=DEFAULT_UPDATE_INTERVAL)  # 30


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up Aussie Broadband sensor from a config entry."""
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    services = hass.data[DOMAIN][entry.entry_id]["services"]

    entities = []
    for service in services:

        async def async_update_data():
            if service["type"] == "PhoneMobile":
                return await client.telephony_usage(service[SERVICE_ID])
            return await client.get_usage(service[SERVICE_ID])

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=service["service_id"],
            update_interval=UPDATE_INTERVAL,
            update_method=async_update_data,
        )
        await coordinator.async_refresh()

        if service["type"] == "PhoneMobile":
            entities.extend(
                [
                    AussieBroadandPhoneInternet(coordinator, service),
                    AussieBroadandPhoneNational(coordinator, service),
                    AussieBroadandPhoneMobile(coordinator, service),
                    AussieBroadandPhoneSMS(coordinator, service),
                    AussieBroadandBillingCycleLength(coordinator, service),
                    AussieBroadandBillingCycleRemaining(coordinator, service),
                ]
            )
        else:
            entities.extend(
                [
                    AussieBroadandTotalUsage(coordinator, service),
                    AussieBroadandDownloaded(coordinator, service),
                    AussieBroadandUploaded(coordinator, service),
                    AussieBroadandBillingCycleLength(coordinator, service),
                    AussieBroadandBillingCycleRemaining(coordinator, service),
                ]
            )

    async_add_entities(entities)
    return True


class AussieBroadandSensorEntity(CoordinatorEntity, SensorEntity):
    """Base class for Aussie Broadband metric sensors."""

    _attribute: str
    _name: str

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        service: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{service[SERVICE_ID]}:{self._attribute}"
        self._attr_name = f"{service['name']} {self._name}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._attribute]


class AussieBroadandTotalUsage(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Total Usage sensor."""

    _attribute = "usedMb"
    _name = "Total Usage"
    _attr_unit_of_measurement = DATA_MEGABYTES
    _attr_state_class = STATE_CLASS_TOTAL_INCREASING


class AussieBroadandDownloaded(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Download Usage sensor."""

    _attribute = "downloadedMb"
    _name = "Downloaded"
    _attr_unit_of_measurement = DATA_MEGABYTES
    _attr_state_class = STATE_CLASS_TOTAL_INCREASING


class AussieBroadandUploaded(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Upload Usage sensor."""

    _attribute = "uploadedMb"
    _name = "Uploaded"
    _attr_unit_of_measurement = DATA_MEGABYTES
    _attr_state_class = STATE_CLASS_TOTAL_INCREASING


class AussieBroadandBillingCycleLength(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Billing Cycle Length sensor."""

    _attribute = "daysTotal"
    _name = "Billing Cycle Length"
    _attr_unit_of_measurement = "days"


class AussieBroadandBillingCycleRemaining(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Billing Cycle Remaining sensor."""

    _attribute = "daysRemaining"
    _name = "Billing Cycle Remaining"
    _attr_unit_of_measurement = "days"


class AussieBroadandPhoneInternet(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Phone Data Usage sensor."""

    _attribute = "internet"
    _name = "Data Used"
    _attr_unit_of_measurement = DATA_KILOBYTES
    _attr_state_class = STATE_CLASS_TOTAL_INCREASING

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._attribute]["kbytes"]


class AussieBroadandPhoneNational(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Phone Data Usaage sensor."""

    _attribute = "national"
    _name = "National Calls"
    _attr_state_class = STATE_CLASS_TOTAL_INCREASING

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._attribute]["calls"]


class AussieBroadandPhoneMobile(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Phone Data Usaage sensor."""

    _attribute = "mobile"
    _name = "Mobile Calls"
    _attr_state_class = STATE_CLASS_TOTAL_INCREASING

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._attribute]["calls"]


class AussieBroadandPhoneSMS(AussieBroadandSensorEntity):
    """Representation of a Aussie Broadband Phone SMS count sensor."""

    _attribute = "sms"
    _name = "SMS Sent"
    _attr_state_class = STATE_CLASS_TOTAL_INCREASING

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._attribute]["calls"]
