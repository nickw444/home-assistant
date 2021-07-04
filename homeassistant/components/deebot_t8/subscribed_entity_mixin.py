from collections import Callable

from deebot_t8 import DeebotEntity

from homeassistant.components.deebot_t8.device_info import get_device_info
from homeassistant.helpers.entity import DeviceInfo, Entity


class SubscribedEntityMixin:
    @property
    def available(self) -> bool:
        return self.api_entity.state.is_online

    @property
    def device_info(self) -> DeviceInfo:
        return get_device_info(self.api_entity)

    def _handle_state_change(self, new_state, attribute):
        self.schedule_update_ha_state()

    async def async_added_to_hass(self) -> None:
        self.api_entity.subscribe(self._handle_state_change)

    async def async_will_remove_from_hass(self) -> None:
        self.api_entity.unsubscribe(self._handle_state_change)
